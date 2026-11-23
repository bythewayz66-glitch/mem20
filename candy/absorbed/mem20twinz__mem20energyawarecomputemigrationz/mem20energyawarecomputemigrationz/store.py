"""SQLite WAL state plane for energy-aware compute migration."""

from __future__ import annotations
import json, sqlite3, threading, time, uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

class StoreError(RuntimeError): pass
class ConflictError(StoreError): pass
class NotFoundError(StoreError): pass

def _j(o): return json.dumps(o, sort_keys=True, default=str)
def _now(): return time.time()

class MigrationStore:
    def __init__(self, path):
        self.path = str(path); Path(self.path).parent.mkdir(parents=True, exist_ok=True); self._lock = threading.RLock(); self._init()
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15); db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL"); db.execute("PRAGMA synchronous=NORMAL"); return db
    def _init(self):
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS objects(kind TEXT,id TEXT,version INTEGER,payload TEXT,updated REAL,PRIMARY KEY(kind,id));
            CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,ts REAL,kind TEXT,payload TEXT);
            CREATE TABLE IF NOT EXISTS migrations(seq INTEGER PRIMARY KEY AUTOINCREMENT,ts REAL,workload_id TEXT,decision TEXT);
            CREATE TABLE IF NOT EXISTS idempotency(key TEXT PRIMARY KEY,result_id TEXT,created_at REAL);
            CREATE TABLE IF NOT EXISTS snapshots(snapshot_id TEXT PRIMARY KEY,label TEXT,created_at REAL,payload TEXT);
            """)
    def _emit(self, db, kind, payload):
        return int(db.execute("INSERT INTO events(ts,kind,payload) VALUES(?,?,?)", (_now(), kind, _j(payload))).lastrowid)
    def put(self, kind, ident, payload, expected_version=None):
        if not ident: raise StoreError("id required")
        with self._lock, self.connect() as db:
            row = db.execute("SELECT version FROM objects WHERE kind=? AND id=?", (kind, ident)).fetchone()
            cur = int(row["version"]) if row else 0
            if expected_version is not None and int(expected_version) != cur: raise ConflictError(f"version conflict {kind}/{ident}: {expected_version}!={cur}")
            ver = cur+1; body = dict(payload); body.setdefault("id", ident)
            db.execute("INSERT INTO objects(kind,id,version,payload,updated) VALUES(?,?,?,?,?) ON CONFLICT(kind,id) DO UPDATE SET version=excluded.version,payload=excluded.payload,updated=excluded.updated", (kind,ident,ver,_j(body),_now()))
            seq = self._emit(db, f"{kind}.upserted", {"kind":kind,"id":ident,"version":ver})
            return {"kind":kind,"id":ident,"version":ver,"payload":body,"event_seq":seq}
    def get(self, kind, ident):
        with self.connect() as db: row = db.execute("SELECT * FROM objects WHERE kind=? AND id=?", (kind, ident)).fetchone()
        if not row: return None
        return {"kind":row["kind"],"id":row["id"],"version":int(row["version"]),"payload":json.loads(row["payload"]),"updated":float(row["updated"])}
    def require(self, kind, ident):
        r = self.get(kind, ident)
        if not r: raise NotFoundError(f"{kind} not found: {ident}")
        return r
    def list(self, kind=None, limit=500):
        with self.connect() as db:
            rows = db.execute("SELECT * FROM objects WHERE kind=? ORDER BY updated DESC LIMIT ?" if kind else "SELECT * FROM objects ORDER BY updated DESC LIMIT ?", ((kind,limit) if kind else (limit,))).fetchall()
        return [{"kind":r["kind"],"id":r["id"],"version":int(r["version"]),"payload":json.loads(r["payload"])} for r in rows]
    def delete(self, kind, ident):
        with self._lock, self.connect() as db:
            n = db.execute("DELETE FROM objects WHERE kind=? AND id=?", (kind,ident)).rowcount
            self._emit(db, f"{kind}.deleted", {"kind":kind,"id":ident,"deleted":bool(n)}); return bool(n)
    def events(self, since=0, limit=200):
        with self.connect() as db: rows = db.execute("SELECT * FROM events WHERE seq>? ORDER BY seq ASC LIMIT ?", (int(since),int(limit))).fetchall()
        return [{"seq":int(r["seq"]),"ts":float(r["ts"]),"kind":r["kind"],"payload":json.loads(r["payload"])} for r in rows]
    def record_migration(self, workload_id, decision):
        with self._lock, self.connect() as db:
            db.execute("INSERT INTO migrations(ts,workload_id,decision) VALUES(?,?,?)", (_now(), workload_id, _j(decision)))
            self._emit(db, "migration.recorded", {"workload_id":workload_id,"to":(decision or {}).get("to")})
    def migrations(self, limit=100):
        with self.connect() as db: rows = db.execute("SELECT * FROM migrations ORDER BY seq DESC LIMIT ?", (int(limit),)).fetchall()
        return [{"seq":int(r["seq"]),"ts":float(r["ts"]),"workload_id":r["workload_id"],"decision":json.loads(r["decision"])} for r in rows]
    def idem_get(self, key):
        if not key: return None
        with self.connect() as db: row = db.execute("SELECT result_id FROM idempotency WHERE key=?", (key,)).fetchone()
        return row["result_id"] if row else None
    def idem_put(self, key, result_id):
        if not key: return
        with self._lock, self.connect() as db: db.execute("INSERT OR REPLACE INTO idempotency(key,result_id,created_at) VALUES(?,?,?)", (key,result_id,_now()))
    def snapshot(self, label=""):
        snap_id = str(uuid.uuid4()); payload = {"objects": self.list(limit=10000)}
        with self._lock, self.connect() as db:
            db.execute("INSERT INTO snapshots(snapshot_id,label,created_at,payload) VALUES(?,?,?,?)", (snap_id,label,_now(),_j(payload)))
            self._emit(db, "snapshot.created", {"snapshot_id":snap_id})
        return {"snapshot_id": snap_id, "label": label, "objects": len(payload["objects"])}
    def restore(self, snapshot_id):
        with self.connect() as db: row = db.execute("SELECT * FROM snapshots WHERE snapshot_id=?", (snapshot_id,)).fetchone()
        if not row: raise NotFoundError(f"snapshot not found: {snapshot_id}")
        payload = json.loads(row["payload"]); objects = payload.get("objects") or []
        with self._lock, self.connect() as db:
            db.execute("DELETE FROM objects")
            for obj in objects: db.execute("INSERT INTO objects(kind,id,version,payload,updated) VALUES(?,?,?,?,?)", (obj["kind"],obj["id"],int(obj.get("version",1)),_j(obj.get("payload") or {}),_now()))
            self._emit(db, "snapshot.restored", {"snapshot_id":snapshot_id,"objects":len(objects)})
        return {"ok": True, "snapshot_id": snapshot_id, "restored_objects": len(objects)}
    def metrics(self):
        with self.connect() as db:
            n = db.execute("SELECT COUNT(*) c FROM objects WHERE kind='node'").fetchone()["c"]
            w = db.execute("SELECT COUNT(*) c FROM objects WHERE kind='workload'").fetchone()["c"]
            e = db.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
            m = db.execute("SELECT COUNT(*) c FROM migrations").fetchone()["c"]
        return {"nodes":int(n),"workloads":int(w),"events":int(e),"migrations":int(m)}
