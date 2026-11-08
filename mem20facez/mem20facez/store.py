"""SQLite-backed durable composition/workspace store for mem20facez (#312)."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


class FacezStore:
    def __init__(self, path: str):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init()

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def _init(self):
        with self._connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS compositions(
              composition_id TEXT PRIMARY KEY, version INTEGER, status TEXT, intent TEXT,
              payload TEXT, plan TEXT, steps TEXT, outputs TEXT, errors TEXT,
              created_at REAL, updated_at REAL
            );
            CREATE TABLE IF NOT EXISTS composition_events(
              seq INTEGER PRIMARY KEY AUTOINCREMENT, composition_id TEXT, ts REAL,
              kind TEXT, payload TEXT
            );
            """)

    def _j(self, o):
        return json.dumps(o, sort_keys=True, default=str)

    def _jl(self, s, default=None):
        return json.loads(s) if s else (default if default is not None else {})

    def event(self, composition_id: str, kind: str, payload: Dict[str, Any], db=None):
        row = (composition_id, time.time(), kind, self._j(payload))
        if db is not None:
            db.execute("INSERT INTO composition_events(composition_id,ts,kind,payload) VALUES(?,?,?,?)", row)
            return
        with self._lock, self._connect() as conn:
            conn.execute("INSERT INTO composition_events(composition_id,ts,kind,payload) VALUES(?,?,?,?)", row)

    def put(self, comp: Dict[str, Any], expected_version: Optional[int] = None) -> Dict[str, Any]:
        cid = str(comp["composition_id"])
        with self._lock, self._connect() as db:
            row = db.execute("SELECT version FROM compositions WHERE composition_id=?", (cid,)).fetchone()
            cur = int(row["version"]) if row else 0
            if expected_version is not None and int(expected_version) != cur:
                raise ValueError(f"version conflict for {cid}: expected {expected_version}, actual {cur}")
            ver = cur + 1
            now = time.time()
            body = dict(comp)
            body["version"] = ver
            body["updated_at"] = now
            body.setdefault("created_at", now)
            db.execute(
                """INSERT INTO compositions(composition_id,version,status,intent,payload,plan,steps,outputs,errors,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(composition_id) DO UPDATE SET
                   version=excluded.version,status=excluded.status,intent=excluded.intent,payload=excluded.payload,
                   plan=excluded.plan,steps=excluded.steps,outputs=excluded.outputs,errors=excluded.errors,updated_at=excluded.updated_at""",
                (cid, ver, str(body.get("status", "")), str(body.get("intent", "")), self._j(body.get("payload") or {}),
                 self._j(body.get("plan") or {}), self._j(body.get("steps") or []), self._j(body.get("outputs") or {}),
                 self._j(body.get("errors") or []), float(body["created_at"]), now),
            )
            self.event(cid, "composition.upserted", {"version": ver, "status": body.get("status")}, db=db)
            return body

    def get(self, composition_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM compositions WHERE composition_id=?", (composition_id,)).fetchone()
        if not row:
            return None
        return {
            "composition_id": row["composition_id"], "version": int(row["version"]), "status": row["status"],
            "intent": row["intent"], "payload": self._jl(row["payload"], {}), "plan": self._jl(row["plan"], {}),
            "steps": self._jl(row["steps"], []), "outputs": self._jl(row["outputs"], {}),
            "errors": self._jl(row["errors"], []), "created_at": float(row["created_at"]), "updated_at": float(row["updated_at"]),
        }

    def list(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT composition_id,version,status,intent,created_at,updated_at FROM compositions ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def history(self, composition_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM composition_events WHERE composition_id=? ORDER BY seq ASC LIMIT ?", (composition_id, limit)).fetchall()
        return [{"seq": int(r["seq"]), "ts": float(r["ts"]), "kind": r["kind"], "payload": self._jl(r["payload"], {})} for r in rows]

    def metrics(self) -> Dict[str, Any]:
        with self._connect() as db:
            c = db.execute("SELECT COUNT(*) n FROM compositions").fetchone()["n"]
            e = db.execute("SELECT COUNT(*) n FROM composition_events").fetchone()["n"]
        return {"compositions": int(c), "events": int(e)}
