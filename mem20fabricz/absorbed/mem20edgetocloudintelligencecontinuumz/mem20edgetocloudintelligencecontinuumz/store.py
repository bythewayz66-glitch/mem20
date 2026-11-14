"""SQLite WAL state plane for the edge-to-cloud intelligence continuum.

Owns: targets, workloads, placement decisions, migrations, events, snapshots,
idempotency keys. Every mutating operation is versioned/conflict-checked or
append-only where appropriate. The store is the durable truth; the service is
the only writer.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .domain import (
    MigrationPlan,
    MigrationState,
    PlacementDecision,
    Target,
    Workload,
    WorkloadState,
)


class NotFoundError(KeyError):
    pass


class ConflictError(RuntimeError):
    pass


_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS targets (
    target_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    version INTEGER NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS workloads (
    workload_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    state TEXT NOT NULL,
    version INTEGER NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS placements (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    placement_id TEXT NOT NULL,
    ts REAL NOT NULL,
    workload_id TEXT NOT NULL,
    chosen TEXT,
    score REAL NOT NULL,
    confidence REAL NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS migrations (
    migration_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    state TEXT NOT NULL,
    version INTEGER NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    ts REAL NOT NULL,
    label TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS idempotency (
    key TEXT PRIMARY KEY,
    workload_id TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_workloads_state ON workloads(state);
CREATE INDEX IF NOT EXISTS idx_events_seq ON events(seq);
"""


class ContinuumStore:
    def __init__(self, path: str | Path):
        self.path = str(Path(path).expanduser())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with self._connect() as db:
            db.executescript(_SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        finally:
            db.close()

    def _event(self, db: sqlite3.Connection, kind: str, payload: dict) -> int:
        cur = db.execute(
            "INSERT INTO events(ts, kind, payload) VALUES (?,?,?)",
            (time.time(), kind, json.dumps(payload, sort_keys=True, default=str)),
        )
        return int(cur.lastrowid)

    # -- targets -----------------------------------------------------------
    def put_target(self, target: Target, *, expected_version: int | None = None) -> dict:
        with self._lock, self._connect() as db:
            row = db.execute("SELECT version FROM targets WHERE target_id=?",
                             (target.target_id,)).fetchone()
            current = int(row["version"]) if row else 0
            if expected_version is not None and current != expected_version:
                raise ConflictError(f"target {target.target_id}: expected {expected_version}, have {current}")
            version = current + 1
            target.version = version
            target.updated_at = time.time()
            payload = json.dumps(target.to_dict(), sort_keys=True)
            db.execute(
                "INSERT INTO targets(target_id,payload,version,updated_at) VALUES (?,?,?,?) "
                "ON CONFLICT(target_id) DO UPDATE SET payload=excluded.payload,version=excluded.version,updated_at=excluded.updated_at",
                (target.target_id, payload, version, target.updated_at),
            )
            seq = self._event(db, "target.upserted", {"target_id": target.target_id, "version": version, "tier": target.tier.value})
            return {"target_id": target.target_id, "version": version, "event_seq": seq}

    def get_target(self, target_id: str) -> Target | None:
        with self._connect() as db:
            row = db.execute("SELECT payload FROM targets WHERE target_id=?", (target_id,)).fetchone()
        return Target.from_dict(json.loads(row["payload"])) if row else None

    def require_target(self, target_id: str) -> Target:
        target = self.get_target(target_id)
        if target is None:
            raise NotFoundError(target_id)
        return target

    def list_targets(self) -> list[Target]:
        with self._connect() as db:
            rows = db.execute("SELECT payload FROM targets ORDER BY target_id").fetchall()
        return [Target.from_dict(json.loads(r["payload"])) for r in rows]

    def delete_target(self, target_id: str, *, expected_version: int | None = None) -> dict:
        with self._lock, self._connect() as db:
            row = db.execute("SELECT version FROM targets WHERE target_id=?", (target_id,)).fetchone()
            if not row:
                raise NotFoundError(target_id)
            if expected_version is not None and int(row["version"]) != expected_version:
                raise ConflictError(f"target {target_id}: expected {expected_version}, have {row['version']}")
            db.execute("DELETE FROM targets WHERE target_id=?", (target_id,))
            seq = self._event(db, "target.deleted", {"target_id": target_id})
            return {"target_id": target_id, "deleted": True, "event_seq": seq}

    # -- workloads ---------------------------------------------------------
    def put_workload(self, workload: Workload, *, expected_version: int | None = None) -> dict:
        with self._lock, self._connect() as db:
            row = db.execute("SELECT version FROM workloads WHERE workload_id=?",
                             (workload.workload_id,)).fetchone()
            current = int(row["version"]) if row else 0
            if expected_version is not None and current != expected_version:
                raise ConflictError(f"workload {workload.workload_id}: expected {expected_version}, have {current}")
            version = current + 1
            workload.version = version
            workload.updated_at = time.time()
            payload = json.dumps(workload.to_dict(), sort_keys=True)
            db.execute(
                "INSERT INTO workloads(workload_id,payload,state,version,updated_at) VALUES (?,?,?,?,?) "
                "ON CONFLICT(workload_id) DO UPDATE SET payload=excluded.payload,state=excluded.state,version=excluded.version,updated_at=excluded.updated_at",
                (workload.workload_id, payload, workload.state.value, version, workload.updated_at),
            )
            seq = self._event(db, "workload.upserted", {"workload_id": workload.workload_id, "version": version, "state": workload.state.value})
            return {"workload_id": workload.workload_id, "version": version, "event_seq": seq}

    def get_workload(self, workload_id: str) -> Workload | None:
        with self._connect() as db:
            row = db.execute("SELECT payload FROM workloads WHERE workload_id=?", (workload_id,)).fetchone()
        return Workload.from_dict(json.loads(row["payload"])) if row else None

    def require_workload(self, workload_id: str) -> Workload:
        workload = self.get_workload(workload_id)
        if workload is None:
            raise NotFoundError(workload_id)
        return workload

    def list_workloads(self, state: str | None = None) -> list[Workload]:
        with self._connect() as db:
            if state:
                rows = db.execute("SELECT payload FROM workloads WHERE state=? ORDER BY updated_at DESC", (state,)).fetchall()
            else:
                rows = db.execute("SELECT payload FROM workloads ORDER BY updated_at DESC").fetchall()
        return [Workload.from_dict(json.loads(r["payload"])) for r in rows]

    # -- placements / migrations / events / snapshots / idempotency ---------
    def record_placement(self, decision: PlacementDecision) -> str:
        placement_id = f"pl-{uuid.uuid4().hex[:12]}"
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO placements(placement_id,ts,workload_id,chosen,score,confidence,payload) VALUES (?,?,?,?,?,?,?)",
                (placement_id, time.time(), decision.workload_id, decision.chosen,
                 decision.score, decision.confidence,
                 json.dumps(decision.to_dict(), sort_keys=True, default=str)),
            )
            self._event(db, "placement.recorded", {"placement_id": placement_id, "workload_id": decision.workload_id, "chosen": decision.chosen, "score": decision.score})
        return placement_id

    def list_placements(self, workload_id: str | None = None, limit: int = 100) -> list[dict]:
        with self._connect() as db:
            if workload_id:
                rows = db.execute("SELECT payload FROM placements WHERE workload_id=? ORDER BY seq DESC LIMIT ?",
                                  (workload_id, limit)).fetchall()
            else:
                rows = db.execute("SELECT payload FROM placements ORDER BY seq DESC LIMIT ?", (limit,)).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def put_migration(self, plan: MigrationPlan, *, expected_version: int | None = None) -> dict:
        with self._lock, self._connect() as db:
            row = db.execute("SELECT version FROM migrations WHERE migration_id=?",
                             (plan.migration_id,)).fetchone()
            current = int(row["version"]) if row else 0
            if expected_version is not None and current != expected_version:
                raise ConflictError(f"migration {plan.migration_id}: expected {expected_version}, have {current}")
            version = current + 1
            payload = json.dumps(plan.to_dict(), sort_keys=True, default=str)
            db.execute(
                "INSERT INTO migrations(migration_id,payload,state,version,updated_at) VALUES (?,?,?,?,?) "
                "ON CONFLICT(migration_id) DO UPDATE SET payload=excluded.payload,state=excluded.state,version=excluded.version,updated_at=excluded.updated_at",
                (plan.migration_id, payload, plan.state.value, version, time.time()),
            )
            seq = self._event(db, "migration.upserted", {"migration_id": plan.migration_id, "version": version, "state": plan.state.value})
            return {"migration_id": plan.migration_id, "version": version, "event_seq": seq}

    def list_migrations(self, limit: int = 100) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT payload FROM migrations ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def events_since(self, since: int = 0, limit: int = 200) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("SELECT seq, ts, kind, payload FROM events WHERE seq>? ORDER BY seq LIMIT ?",
                              (int(since), int(limit))).fetchall()
        return [{"seq": r["seq"], "ts": r["ts"], "kind": r["kind"], "payload": json.loads(r["payload"])} for r in rows]

    def snapshot(self, label: str = "") -> dict:
        snapshot_id = f"snap-{uuid.uuid4().hex[:12]}"
        payload = {
            "targets": [t.to_dict() for t in self.list_targets()],
            "workloads": [w.to_dict() for w in self.list_workloads()],
            "migrations": self.list_migrations(limit=10000),
        }
        with self._lock, self._connect() as db:
            db.execute("INSERT INTO snapshots(snapshot_id,ts,label,payload) VALUES (?,?,?,?)",
                       (snapshot_id, time.time(), label or snapshot_id, json.dumps(payload, sort_keys=True, default=str)))
            self._event(db, "snapshot.created", {"snapshot_id": snapshot_id, "label": label})
        return {"snapshot_id": snapshot_id, "label": label or snapshot_id, "targets": len(payload["targets"]), "workloads": len(payload["workloads"])}

    def restore(self, snapshot_id: str) -> dict:
        with self._lock, self._connect() as db:
            row = db.execute("SELECT payload FROM snapshots WHERE snapshot_id=?", (snapshot_id,)).fetchone()
            if not row:
                raise NotFoundError(snapshot_id)
            payload = json.loads(row["payload"])
            db.execute("DELETE FROM targets")
            db.execute("DELETE FROM workloads")
            db.execute("DELETE FROM migrations")
            for item in payload.get("targets", []):
                target = Target.from_dict(item)
                db.execute("INSERT INTO targets(target_id,payload,version,updated_at) VALUES (?,?,?,?)",
                           (target.target_id, json.dumps(target.to_dict(), sort_keys=True), int(item.get("version", 1)), time.time()))
            for item in payload.get("workloads", []):
                workload = Workload.from_dict(item)
                db.execute("INSERT INTO workloads(workload_id,payload,state,version,updated_at) VALUES (?,?,?,?,?)",
                           (workload.workload_id, json.dumps(workload.to_dict(), sort_keys=True), workload.state.value, int(item.get("version", 1)), time.time()))
            for item in payload.get("migrations", []):
                mid = item.get("migration_id") or f"mig-{uuid.uuid4().hex[:8]}"
                db.execute("INSERT OR REPLACE INTO migrations(migration_id,payload,state,version,updated_at) VALUES (?,?,?,?,?)",
                           (mid, json.dumps(item, sort_keys=True, default=str), item.get("state", "planned"), int(item.get("version", 1)), time.time()))
            self._event(db, "snapshot.restored", {"snapshot_id": snapshot_id})
        return {"restored": True, "snapshot_id": snapshot_id, "targets": len(payload.get("targets", [])), "workloads": len(payload.get("workloads", []))}

    def idempotency_lookup(self, key: str) -> str | None:
        if not key:
            return None
        with self._connect() as db:
            row = db.execute("SELECT workload_id FROM idempotency WHERE key=?", (key,)).fetchone()
        return row["workload_id"] if row else None

    def idempotency_store(self, key: str, workload_id: str) -> None:
        if not key:
            return
        with self._lock, self._connect() as db:
            db.execute("INSERT OR IGNORE INTO idempotency(key,workload_id,created_at) VALUES (?,?,?)",
                       (key, workload_id, time.time()))

    def metrics(self) -> dict:
        with self._connect() as db:
            def count(sql: str, *args) -> int:
                return int(db.execute(sql, args).fetchone()[0])
            return {
                "store_path": self.path,
                "targets": count("SELECT COUNT(*) FROM targets"),
                "workloads": count("SELECT COUNT(*) FROM workloads"),
                "placements": count("SELECT COUNT(*) FROM placements"),
                "migrations": count("SELECT COUNT(*) FROM migrations"),
                "events": count("SELECT COUNT(*) FROM events"),
                "snapshots": count("SELECT COUNT(*) FROM snapshots"),
                "idempotency_keys": count("SELECT COUNT(*) FROM idempotency"),
            }
