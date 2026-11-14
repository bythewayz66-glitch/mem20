"""SQLite WAL store for episodic memory graph."""
from __future__ import annotations
import json, sqlite3, threading, time, uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

class StoreError(RuntimeError): pass
class NotFoundError(StoreError): pass
class ConflictError(StoreError): pass

def _j(o): return json.dumps(o, sort_keys=True, default=str)
def _now(): return time.time()

class EpisodicStore:
    def __init__(self, path):
        self.path = str(path); Path(self.path).parent.mkdir(parents=True, exist_ok=True); self._lock = threading.RLock(); self._init()
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15); db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL"); db.execute("PRAGMA synchronous=NORMAL"); db.execute("PRAGMA foreign_keys=ON"); return db
    def _init(self):
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS episodes(id TEXT PRIMARY KEY,version INTEGER,title TEXT,payload TEXT,created_at REAL,updated REAL);
            CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,ts REAL,kind TEXT,payload TEXT);
            CREATE TABLE IF NOT EXISTS snapshots(snapshot_id TEXT PRIMARY KEY,label TEXT,created_at REAL,payload TEXT);
            """)
    def _emit(self, db, kind, payload): return int(db.execute("INSERT INTO events(ts,kind,payload) VALUES(?,?,?)", (_now(), kind, _j(payload))).lastrowid)
    def put_episode(self, episode: Dict[str, Any], expected_version=None):
        eid = str(episode.get("id") or episode.get("episode_id") or "")
        if not eid: raise StoreError("episode id required")
        with self._lock, self.connect() as db:
            row = db.execute("SELECT version FROM episodes WHERE id=?", (eid,)).fetchone()
            cur = int(row["version"]) if row else 0
            if expected_version is not None and int(expected_version) != cur: raise ConflictError(f"version conflict episode/{eid}: {expected_version}!={cur}")
            ver = cur + 1; body = dict(episode); body["id"] = eid; body["version"] = ver
            db.execute("INSERT INTO episodes(id,version,title,payload,created_at,updated) VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET version=excluded.version,title=excluded.title,payload=excluded.payload,updated=excluded.updated",
                       (eid, ver, str(body.get("title","")), _j(body), float(body.get("created_at", _now()) or _now()), _now()))
            self._emit(db, "episode.upserted", {"id": eid, "version": ver})
            return body
    def get_episode(self, episode_id):
        with self.connect() as db: row = db.execute("SELECT payload FROM episodes WHERE id=?", (episode_id,)).fetchone()
        return json.loads(row["payload"]) if row else None
    def require_episode(self, episode_id):
        ep = self.get_episode(episode_id)
        if not ep: raise NotFoundError(f"episode not found: {episode_id}")
        return ep
    def list_episodes(self, limit=500):
        with self.connect() as db: rows = db.execute("SELECT payload FROM episodes ORDER BY updated DESC LIMIT ?", (limit,)).fetchall()
        return [json.loads(r["payload"]) for r in rows]
    def delete_episode(self, episode_id):
        with self._lock, self.connect() as db:
            n = db.execute("DELETE FROM episodes WHERE id=?", (episode_id,)).rowcount
            self._emit(db, "episode.deleted", {"id": episode_id, "deleted": bool(n)}); return bool(n)
    def events(self, since=0, limit=200):
        with self.connect() as db: rows = db.execute("SELECT * FROM events WHERE seq>? ORDER BY seq ASC LIMIT ?", (int(since), int(limit))).fetchall()
        return [{"seq": int(r["seq"]), "ts": float(r["ts"]), "kind": r["kind"], "payload": json.loads(r["payload"])} for r in rows]
    def snapshot(self, label=""):
        sid = str(uuid.uuid4())
        with self._lock, self.connect() as db:
            db.execute("INSERT INTO snapshots(snapshot_id,label,created_at,payload) VALUES(?,?,?,?)", (sid, label, _now(), _j({"episodes": self.list_episodes(10000)})))
            self._emit(db, "snapshot.created", {"snapshot_id": sid})
        return {"snapshot_id": sid, "label": label}
    def restore(self, snapshot_id):
        with self.connect() as db: row = db.execute("SELECT payload FROM snapshots WHERE snapshot_id=?", (snapshot_id,)).fetchone()
        if not row: raise NotFoundError(f"snapshot not found: {snapshot_id}")
        episodes = (json.loads(row["payload"]) or {}).get("episodes") or []
        with self._lock, self.connect() as db:
            db.execute("DELETE FROM episodes")
            for ep in episodes:
                db.execute("INSERT INTO episodes(id,version,title,payload,created_at,updated) VALUES(?,?,?,?,?,?)",
                           (ep.get("id"), int(ep.get("version",1)), str(ep.get("title","")), _j(ep), float(ep.get("created_at",_now()) or _now()), _now()))
            self._emit(db, "snapshot.restored", {"snapshot_id": snapshot_id, "episodes": len(episodes)})
        return {"ok": True, "snapshot_id": snapshot_id, "restored": len(episodes)}
    def metrics(self):
        with self.connect() as db:
            return {"episodes": int(db.execute("SELECT COUNT(*) c FROM episodes").fetchone()["c"]), "events": int(db.execute("SELECT COUNT(*) c FROM events").fetchone()["c"])}
