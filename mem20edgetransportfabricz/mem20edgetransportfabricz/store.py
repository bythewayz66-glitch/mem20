"""SQLite WAL state plane for the edge transport fabric.

Durable objects: nodes, links, flows, reservations/placements, events,
snapshots. Versioned upserts, append-only events, idempotency support.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class StoreError(RuntimeError):
    pass


class ConflictError(StoreError):
    pass


class NotFoundError(StoreError):
    pass


def _now() -> float:
    return time.time()


def _j(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


class FabricStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init()

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=NORMAL")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def _init(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS objects(
                  kind TEXT NOT NULL,
                  id TEXT NOT NULL,
                  version INTEGER NOT NULL,
                  payload TEXT NOT NULL,
                  updated REAL NOT NULL,
                  PRIMARY KEY(kind,id)
                );
                CREATE TABLE IF NOT EXISTS events(
                  seq INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts REAL NOT NULL,
                  kind TEXT NOT NULL,
                  payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS placements(
                  seq INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts REAL NOT NULL,
                  flow_id TEXT NOT NULL,
                  decision TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS idempotency(
                  key TEXT PRIMARY KEY,
                  result_id TEXT NOT NULL,
                  created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS snapshots(
                  snapshot_id TEXT PRIMARY KEY,
                  label TEXT,
                  created_at REAL NOT NULL,
                  payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_objects_kind ON objects(kind, updated DESC);
                CREATE INDEX IF NOT EXISTS idx_events_seq ON events(seq);
                CREATE INDEX IF NOT EXISTS idx_placements_flow ON placements(flow_id, seq DESC);
                """
            )

    def _emit(self, db: sqlite3.Connection, kind: str, payload: Dict[str, Any]) -> int:
        cur = db.execute("INSERT INTO events(ts,kind,payload) VALUES(?,?,?)", (_now(), kind, _j(payload)))
        return int(cur.lastrowid)

    def put(self, kind: str, ident: str, payload: Dict[str, Any], expected_version: Optional[int] = None) -> Dict[str, Any]:
        if not ident or not str(ident).strip():
            raise StoreError("id is required")
        if not isinstance(payload, dict):
            raise StoreError("payload must be an object")
        with self._lock, self.connect() as db:
            row = db.execute("SELECT version FROM objects WHERE kind=? AND id=?", (kind, ident)).fetchone()
            cur = int(row["version"]) if row else 0
            if expected_version is not None and int(expected_version) != cur:
                raise ConflictError(f"version conflict for {kind}/{ident}: expected {expected_version}, actual {cur}")
            ver = cur + 1
            now = _now()
            body = dict(payload)
            body.setdefault("id", ident)
            db.execute(
                "INSERT INTO objects(kind,id,version,payload,updated) VALUES(?,?,?,?,?) "
                "ON CONFLICT(kind,id) DO UPDATE SET version=excluded.version,payload=excluded.payload,updated=excluded.updated",
                (kind, ident, ver, _j(body), now),
            )
            seq = self._emit(db, f"{kind}.upserted", {"kind": kind, "id": ident, "version": ver})
            return {"kind": kind, "id": ident, "version": ver, "payload": body, "updated": now, "event_seq": seq}

    def get(self, kind: str, ident: str) -> Optional[Dict[str, Any]]:
        with self.connect() as db:
            row = db.execute("SELECT * FROM objects WHERE kind=? AND id=?", (kind, ident)).fetchone()
        if not row:
            return None
        return {"kind": row["kind"], "id": row["id"], "version": int(row["version"]), "payload": json.loads(row["payload"]), "updated": float(row["updated"])}

    def require(self, kind: str, ident: str) -> Dict[str, Any]:
        row = self.get(kind, ident)
        if not row:
            raise NotFoundError(f"{kind} not found: {ident}")
        return row

    def list(self, kind: Optional[str] = None, limit: int = 500) -> List[Dict[str, Any]]:
        limit = max(1, min(int(limit), 5000))
        with self.connect() as db:
            if kind:
                rows = db.execute("SELECT * FROM objects WHERE kind=? ORDER BY updated DESC LIMIT ?", (kind, limit)).fetchall()
            else:
                rows = db.execute("SELECT * FROM objects ORDER BY updated DESC LIMIT ?", (limit,)).fetchall()
        return [{"kind": r["kind"], "id": r["id"], "version": int(r["version"]), "payload": json.loads(r["payload"]), "updated": float(r["updated"])} for r in rows]

    def delete(self, kind: str, ident: str) -> bool:
        with self._lock, self.connect() as db:
            n = db.execute("DELETE FROM objects WHERE kind=? AND id=?", (kind, ident)).rowcount
            self._emit(db, f"{kind}.deleted", {"kind": kind, "id": ident, "deleted": bool(n)})
            return bool(n)

    def events(self, since: int = 0, limit: int = 200) -> List[Dict[str, Any]]:
        limit = max(1, min(int(limit), 2000))
        with self.connect() as db:
            rows = db.execute("SELECT * FROM events WHERE seq>? ORDER BY seq ASC LIMIT ?", (int(since), limit)).fetchall()
        return [{"seq": int(r["seq"]), "ts": float(r["ts"]), "kind": r["kind"], "payload": json.loads(r["payload"])} for r in rows]

    def record_placement(self, flow_id: str, decision: Dict[str, Any]) -> int:
        with self._lock, self.connect() as db:
            cur = db.execute("INSERT INTO placements(ts,flow_id,decision) VALUES(?,?,?)", (_now(), flow_id, _j(decision)))
            seq = self._emit(db, "flow.placement", {"flow_id": flow_id, "admitted": decision.get("admitted"), "path": decision.get("path")})
            return int(cur.lastrowid) or seq

    def placements(self, flow_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        limit = max(1, min(int(limit), 1000))
        with self.connect() as db:
            if flow_id:
                rows = db.execute("SELECT * FROM placements WHERE flow_id=? ORDER BY seq DESC LIMIT ?", (flow_id, limit)).fetchall()
            else:
                rows = db.execute("SELECT * FROM placements ORDER BY seq DESC LIMIT ?", (limit,)).fetchall()
        return [{"seq": int(r["seq"]), "ts": float(r["ts"]), "flow_id": r["flow_id"], "decision": json.loads(r["decision"])} for r in rows]

    def idem_get(self, key: str) -> Optional[str]:
        if not key:
            return None
        with self.connect() as db:
            row = db.execute("SELECT result_id FROM idempotency WHERE key=?", (key,)).fetchone()
        return row["result_id"] if row else None

    def idem_put(self, key: str, result_id: str) -> None:
        if not key:
            return
        with self._lock, self.connect() as db:
            db.execute("INSERT OR REPLACE INTO idempotency(key,result_id,created_at) VALUES(?,?,?)", (key, result_id, _now()))

    def snapshot(self, label: str = "") -> Dict[str, Any]:
        snap_id = str(uuid.uuid4())
        payload = {
            "objects": self.list(limit=10000),
            "events_tail": self.events(max(0, self._max_seq() - 500), 500),
            "placements_tail": self.placements(limit=200),
        }
        with self._lock, self.connect() as db:
            db.execute("INSERT INTO snapshots(snapshot_id,label,created_at,payload) VALUES(?,?,?,?)", (snap_id, label or "", _now(), _j(payload)))
            self._emit(db, "snapshot.created", {"snapshot_id": snap_id, "label": label})
        return {"snapshot_id": snap_id, "label": label, "objects": len(payload["objects"])}

    def _max_seq(self) -> int:
        with self.connect() as db:
            row = db.execute("SELECT COALESCE(MAX(seq),0) AS m FROM events").fetchone()
        return int(row["m"]) if row else 0

    def restore(self, snapshot_id: str) -> Dict[str, Any]:
        with self.connect() as db:
            row = db.execute("SELECT * FROM snapshots WHERE snapshot_id=?", (snapshot_id,)).fetchone()
        if not row:
            raise NotFoundError(f"snapshot not found: {snapshot_id}")
        payload = json.loads(row["payload"])
        objects = payload.get("objects") or []
        with self._lock, self.connect() as db:
            db.execute("DELETE FROM objects")
            for obj in objects:
                db.execute("INSERT INTO objects(kind,id,version,payload,updated) VALUES(?,?,?,?,?)",
                           (obj["kind"], obj["id"], int(obj.get("version", 1)), _j(obj.get("payload") or {}), float(obj.get("updated") or _now())))
            self._emit(db, "snapshot.restored", {"snapshot_id": snapshot_id, "objects": len(objects)})
        return {"ok": True, "snapshot_id": snapshot_id, "restored_objects": len(objects)}

    def metrics(self) -> Dict[str, Any]:
        with self.connect() as db:
            counts = {}
            for kind in ("node", "link", "flow"):
                row = db.execute("SELECT COUNT(*) AS c FROM objects WHERE kind=?", (kind,)).fetchone()
                counts[kind + "s"] = int(row["c"]) if row else 0
            ev = db.execute("SELECT COUNT(*) AS c FROM events").fetchone()
            pl = db.execute("SELECT COUNT(*) AS c FROM placements").fetchone()
            sn = db.execute("SELECT COUNT(*) AS c FROM snapshots").fetchone()
        return {**counts, "events": int(ev["c"]), "placements": int(pl["c"]), "snapshots": int(sn["c"]), "max_event_seq": self._max_seq()}
