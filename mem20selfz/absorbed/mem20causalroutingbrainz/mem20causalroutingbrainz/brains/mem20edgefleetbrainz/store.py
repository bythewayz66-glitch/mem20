"""Persistent state plane for the edge fleet brain.

SQLite in WAL mode, because the fleet is written from the scheduler thread and
read from HTTP handlers at the same time, and because an edge box loses power:
a committed placement must survive a hard reset without a repair pass.

Three shapes are stored separately rather than in one blob table:

* ``nodes`` and ``workloads`` carry a monotonic ``version`` so two writers
  cannot silently overwrite each other (optimistic concurrency);
* ``placements`` is an append-only decision journal, because "why did the
  scheduler pick that node" is the question an operator asks after an incident;
* ``events`` is the subscription stream the HTTP surface polls, and
  ``snapshots`` is a whole-fleet point-in-time copy for rollback.

Idempotency keys live in their own table so a retried submission returns the
original workload instead of creating a duplicate.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

from .domain import Node, PlacementDecision, Workload, WorkloadState

__all__ = ["ConflictError", "FleetStore", "NotFoundError"]


class ConflictError(RuntimeError):
    """The caller's expected version does not match the stored one."""


class NotFoundError(KeyError):
    """The requested object does not exist."""


class FleetStore:
    """SQLite-backed state plane with versions, events and snapshots."""

    SCHEMA = """
    PRAGMA journal_mode=WAL;
    PRAGMA synchronous=NORMAL;
    PRAGMA foreign_keys=ON;

    CREATE TABLE IF NOT EXISTS nodes (
        node_id   TEXT PRIMARY KEY,
        payload   TEXT NOT NULL,
        version   INTEGER NOT NULL,
        updated   REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS workloads (
        workload_id TEXT PRIMARY KEY,
        state       TEXT NOT NULL,
        payload     TEXT NOT NULL,
        version     INTEGER NOT NULL,
        updated     REAL NOT NULL
    );
    CREATE INDEX IF NOT EXISTS workloads_state ON workloads(state);

    CREATE TABLE IF NOT EXISTS placements (
        seq         INTEGER PRIMARY KEY AUTOINCREMENT,
        ts          REAL NOT NULL,
        workload_id TEXT NOT NULL,
        chosen      TEXT,
        payload     TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS events (
        seq     INTEGER PRIMARY KEY AUTOINCREMENT,
        ts      REAL NOT NULL,
        kind    TEXT NOT NULL,
        payload TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS snapshots (
        snapshot_id TEXT PRIMARY KEY,
        ts          REAL NOT NULL,
        label       TEXT NOT NULL,
        payload     TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS idempotency (
        key         TEXT PRIMARY KEY,
        workload_id TEXT NOT NULL,
        ts          REAL NOT NULL
    );
    """

    def __init__(self, path: str | Path) -> None:
        self.path = str(Path(path).expanduser())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with self._connect() as db:
            db.executescript(self.SCHEMA)

    # -- plumbing -----------------------------------------------------
    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=30.0)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _event(db: sqlite3.Connection, kind: str, payload: dict) -> int:
        cur = db.execute(
            "INSERT INTO events(ts, kind, payload) VALUES (?, ?, ?)",
            (time.time(), kind, json.dumps(payload, sort_keys=True, default=str)),
        )
        return int(cur.lastrowid)

    # -- nodes --------------------------------------------------------
    def put_node(self, node: Node, expected_version: int | None = None) -> dict:
        with self._lock, self._connect() as db:
            row = db.execute("SELECT version FROM nodes WHERE node_id=?", (node.node_id,)).fetchone()
            current = int(row["version"]) if row else 0
            if expected_version is not None and expected_version != current:
                raise ConflictError(
                    f"node {node.node_id}: expected version {expected_version}, stored {current}")
            version = current + 1
            db.execute(
                "INSERT INTO nodes(node_id, payload, version, updated) VALUES (?,?,?,?) "
                "ON CONFLICT(node_id) DO UPDATE SET payload=excluded.payload, "
                "version=excluded.version, updated=excluded.updated",
                (node.node_id, json.dumps(node.to_dict(), sort_keys=True), version, time.time()),
            )
            seq = self._event(db, "node.upserted",
                              {"node_id": node.node_id, "version": version,
                               "status": node.status.value})
            return {"node_id": node.node_id, "version": version, "event_seq": seq}

    def get_node(self, node_id: str) -> Node | None:
        with self._connect() as db:
            row = db.execute("SELECT payload FROM nodes WHERE node_id=?", (node_id,)).fetchone()
        return None if row is None else Node.from_dict(json.loads(row["payload"]))

    def require_node(self, node_id: str) -> Node:
        node = self.get_node(node_id)
        if node is None:
            raise NotFoundError(node_id)
        return node

    def node_version(self, node_id: str) -> int:
        with self._connect() as db:
            row = db.execute("SELECT version FROM nodes WHERE node_id=?", (node_id,)).fetchone()
        if row is None:
            raise NotFoundError(node_id)
        return int(row["version"])

    def list_nodes(self) -> list[Node]:
        with self._connect() as db:
            rows = db.execute("SELECT payload FROM nodes ORDER BY node_id").fetchall()
        return [Node.from_dict(json.loads(r["payload"])) for r in rows]

    def delete_node(self, node_id: str, expected_version: int | None = None) -> dict:
        with self._lock, self._connect() as db:
            row = db.execute("SELECT version FROM nodes WHERE node_id=?", (node_id,)).fetchone()
            if row is None:
                raise NotFoundError(node_id)
            current = int(row["version"])
            if expected_version is not None and expected_version != current:
                raise ConflictError(
                    f"node {node_id}: expected version {expected_version}, stored {current}")
            db.execute("DELETE FROM nodes WHERE node_id=?", (node_id,))
            seq = self._event(db, "node.deleted", {"node_id": node_id, "version": current})
            return {"node_id": node_id, "deleted": True, "event_seq": seq}

    # -- workloads ----------------------------------------------------
    def put_workload(self, workload: Workload, expected_version: int | None = None) -> dict:
        with self._lock, self._connect() as db:
            row = db.execute(
                "SELECT version FROM workloads WHERE workload_id=?",
                (workload.workload_id,),
            ).fetchone()
            current = int(row["version"]) if row else 0
            if expected_version is not None and expected_version != current:
                raise ConflictError(
                    f"workload {workload.workload_id}: expected version "
                    f"{expected_version}, stored {current}")
            version = current + 1
            db.execute(
                "INSERT INTO workloads(workload_id, state, payload, version, updated) "
                "VALUES (?,?,?,?,?) ON CONFLICT(workload_id) DO UPDATE SET "
                "state=excluded.state, payload=excluded.payload, "
                "version=excluded.version, updated=excluded.updated",
                (workload.workload_id, workload.state.value,
                 json.dumps(workload.to_dict(), sort_keys=True), version, time.time()),
            )
            seq = self._event(db, "workload.upserted",
                              {"workload_id": workload.workload_id, "version": version,
                               "state": workload.state.value,
                               "assigned_node": workload.assigned_node})
            return {"workload_id": workload.workload_id, "version": version, "event_seq": seq}

    def get_workload(self, workload_id: str) -> Workload | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT payload FROM workloads WHERE workload_id=?", (workload_id,)
            ).fetchone()
        return None if row is None else Workload.from_dict(json.loads(row["payload"]))

    def require_workload(self, workload_id: str) -> Workload:
        workload = self.get_workload(workload_id)
        if workload is None:
            raise NotFoundError(workload_id)
        return workload

    def workload_version(self, workload_id: str) -> int:
        with self._connect() as db:
            row = db.execute(
                "SELECT version FROM workloads WHERE workload_id=?", (workload_id,)
            ).fetchone()
        if row is None:
            raise NotFoundError(workload_id)
        return int(row["version"])

    def list_workloads(self, state: WorkloadState | str | None = None) -> list[Workload]:
        sql = "SELECT payload FROM workloads"
        params: tuple = ()
        if state is not None:
            value = state.value if isinstance(state, WorkloadState) else str(state)
            sql += " WHERE state=?"
            params = (value,)
        sql += " ORDER BY workload_id"
        with self._connect() as db:
            rows = db.execute(sql, params).fetchall()
        return [Workload.from_dict(json.loads(r["payload"])) for r in rows]

    def delete_workload(self, workload_id: str) -> dict:
        with self._lock, self._connect() as db:
            row = db.execute(
                "SELECT version FROM workloads WHERE workload_id=?", (workload_id,)
            ).fetchone()
            if row is None:
                raise NotFoundError(workload_id)
            db.execute("DELETE FROM workloads WHERE workload_id=?", (workload_id,))
            seq = self._event(db, "workload.deleted",
                              {"workload_id": workload_id, "version": int(row["version"])})
            return {"workload_id": workload_id, "deleted": True, "event_seq": seq}

    # -- decisions ----------------------------------------------------
    def record_placement(self, decision: PlacementDecision) -> int:
        with self._lock, self._connect() as db:
            cur = db.execute(
                "INSERT INTO placements(ts, workload_id, chosen, payload) VALUES (?,?,?,?)",
                (time.time(), decision.workload_id, decision.chosen,
                 json.dumps(decision.to_dict(), sort_keys=True, default=str)),
            )
            seq = self._event(db, "placement.decided", {
                "workload_id": decision.workload_id,
                "chosen": decision.chosen,
                "score": decision.score,
                "confidence": decision.confidence,
                "bottlenecks": decision.bottlenecks,
            })
            return int(cur.lastrowid)

    def list_placements(self, limit: int = 50) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT seq, ts, workload_id, chosen, payload FROM placements "
                "ORDER BY seq DESC LIMIT ?", (int(limit),)
            ).fetchall()
        out = []
        for row in rows:
            item = json.loads(row["payload"])
            item["seq"] = int(row["seq"])
            item["ts"] = float(row["ts"])
            out.append(item)
        return out

    # -- events -------------------------------------------------------
    def append_event(self, kind: str, payload: dict) -> int:
        with self._lock, self._connect() as db:
            return self._event(db, kind, payload)

    def events_since(self, seq: int = 0, limit: int = 200) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT seq, ts, kind, payload FROM events WHERE seq > ? "
                "ORDER BY seq ASC LIMIT ?", (int(seq), int(limit))
            ).fetchall()
        return [
            {"seq": int(r["seq"]), "ts": float(r["ts"]), "kind": r["kind"],
             "payload": json.loads(r["payload"])}
            for r in rows
        ]

    def latest_event_seq(self) -> int:
        with self._connect() as db:
            row = db.execute("SELECT COALESCE(MAX(seq), 0) AS seq FROM events").fetchone()
        return int(row["seq"])

    # -- snapshots ----------------------------------------------------
    def snapshot(self, label: str = "") -> dict:
        with self._lock, self._connect() as db:
            nodes = [json.loads(r["payload"]) for r in
                     db.execute("SELECT payload FROM nodes ORDER BY node_id")]
            workloads = [json.loads(r["payload"]) for r in
                         db.execute("SELECT payload FROM workloads ORDER BY workload_id")]
            snapshot_id = "snap-" + uuid.uuid4().hex[:12]
            payload = {"nodes": nodes, "workloads": workloads}
            db.execute(
                "INSERT INTO snapshots(snapshot_id, ts, label, payload) VALUES (?,?,?,?)",
                (snapshot_id, time.time(), label,
                 json.dumps(payload, sort_keys=True)),
            )
            self._event(db, "snapshot.created",
                        {"snapshot_id": snapshot_id, "label": label,
                         "nodes": len(nodes), "workloads": len(workloads)})
            return {"snapshot_id": snapshot_id, "label": label,
                    "nodes": len(nodes), "workloads": len(workloads)}

    def list_snapshots(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT snapshot_id, ts, label, payload FROM snapshots ORDER BY ts DESC"
            ).fetchall()
        return [
            {"snapshot_id": r["snapshot_id"], "ts": float(r["ts"]), "label": r["label"],
             "nodes": len(json.loads(r["payload"]).get("nodes", [])),
             "workloads": len(json.loads(r["payload"]).get("workloads", []))}
            for r in rows
        ]

    def restore(self, snapshot_id: str) -> dict:
        with self._lock, self._connect() as db:
            row = db.execute(
                "SELECT payload FROM snapshots WHERE snapshot_id=?", (snapshot_id,)
            ).fetchone()
            if row is None:
                raise NotFoundError(snapshot_id)
            payload = json.loads(row["payload"])
            db.execute("DELETE FROM nodes")
            db.execute("DELETE FROM workloads")
            for node in payload.get("nodes", []):
                db.execute(
                    "INSERT INTO nodes(node_id, payload, version, updated) VALUES (?,?,?,?)",
                    (node["node_id"], json.dumps(node, sort_keys=True), 1, time.time()),
                )
            for workload in payload.get("workloads", []):
                db.execute(
                    "INSERT INTO workloads(workload_id, state, payload, version, updated) "
                    "VALUES (?,?,?,?,?)",
                    (workload["workload_id"], workload.get("state", "queued"),
                     json.dumps(workload, sort_keys=True), 1, time.time()),
                )
            self._event(db, "snapshot.restored",
                        {"snapshot_id": snapshot_id,
                         "nodes": len(payload.get("nodes", [])),
                         "workloads": len(payload.get("workloads", []))})
            return {"snapshot_id": snapshot_id, "restored": True,
                    "nodes": len(payload.get("nodes", [])),
                    "workloads": len(payload.get("workloads", []))}

    # -- idempotency --------------------------------------------------
    def claim_key(self, key: str, workload_id: str) -> bool:
        """Return True when ``key`` is new and was claimed, False when it exists."""
        if not key:
            return True
        with self._lock, self._connect() as db:
            try:
                db.execute(
                    "INSERT INTO idempotency(key, workload_id, ts) VALUES (?,?,?)",
                    (str(key), str(workload_id), time.time()),
                )
            except sqlite3.IntegrityError:
                return False
            self._event(db, "idempotency.claimed",
                        {"key": str(key), "workload_id": str(workload_id)})
            return True

    def lookup_key(self, key: str) -> str | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT workload_id FROM idempotency WHERE key=?", (str(key),)
            ).fetchone()
        return None if row is None else str(row["workload_id"])

    # -- metrics ------------------------------------------------------
    def metrics(self) -> dict:
        with self._connect() as db:
            node_count = int(db.execute("SELECT COUNT(*) AS n FROM nodes").fetchone()["n"])
            workload_count = int(
                db.execute("SELECT COUNT(*) AS n FROM workloads").fetchone()["n"])
            placement_count = int(
                db.execute("SELECT COUNT(*) AS n FROM placements").fetchone()["n"])
            event_count = int(db.execute("SELECT COUNT(*) AS n FROM events").fetchone()["n"])
            snapshot_count = int(
                db.execute("SELECT COUNT(*) AS n FROM snapshots").fetchone()["n"])
        return {
            "store_path": self.path,
            "nodes": node_count,
            "workloads": workload_count,
            "placements": placement_count,
            "events": event_count,
            "snapshots": snapshot_count,
            "latest_event_seq": self.latest_event_seq(),
        }
