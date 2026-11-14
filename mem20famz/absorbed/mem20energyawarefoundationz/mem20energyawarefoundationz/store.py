from __future__ import annotations
import json, sqlite3, threading, time, uuid
from pathlib import Path
class StoreError(RuntimeError): pass
class NotFoundError(StoreError): pass
class ConflictError(StoreError): pass
def _j(o): return json.dumps(o, sort_keys=True, default=str)
class FoundationStore:
    def __init__(self, path):
        self.path=str(path); Path(self.path).parent.mkdir(parents=True, exist_ok=True); self._lock=threading.RLock(); self._init()
    def connect(self): db=sqlite3.connect(self.path, timeout=15); db.row_factory=sqlite3.Row; db.execute("PRAGMA journal_mode=WAL"); return db
    def _init(self):
        with self.connect() as db: db.executescript("CREATE TABLE IF NOT EXISTS objects(kind TEXT,id TEXT,version INTEGER,payload TEXT,updated REAL,PRIMARY KEY(kind,id)); CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,ts REAL,kind TEXT,payload TEXT); CREATE TABLE IF NOT EXISTS snapshots(snapshot_id TEXT PRIMARY KEY,label TEXT,created_at REAL,payload TEXT);")
    def _emit(self,db,kind,payload): return int(db.execute("INSERT INTO events(ts,kind,payload) VALUES(?,?,?)",(time.time(),kind,_j(payload))).lastrowid)
    def put(self,kind,ident,payload,expected_version=None):
        with self._lock,self.connect() as db:
            row=db.execute("SELECT version FROM objects WHERE kind=? AND id=?",(kind,ident)).fetchone(); cur=int(row["version"]) if row else 0
            if expected_version is not None and int(expected_version)!=cur: raise ConflictError(f"version conflict {kind}/{ident}")
            ver=cur+1; body=dict(payload); body.setdefault("id",ident)
            db.execute("INSERT INTO objects(kind,id,version,payload,updated) VALUES(?,?,?,?,?) ON CONFLICT(kind,id) DO UPDATE SET version=excluded.version,payload=excluded.payload,updated=excluded.updated",(kind,ident,ver,_j(body),time.time()))
            self._emit(db,f"{kind}.upserted",{"kind":kind,"id":ident,"version":ver}); return {"kind":kind,"id":ident,"version":ver,"payload":body}
    def get(self,kind,ident):
        with self.connect() as db: row=db.execute("SELECT * FROM objects WHERE kind=? AND id=?",(kind,ident)).fetchone()
        return {"kind":row["kind"],"id":row["id"],"version":int(row["version"]),"payload":json.loads(row["payload"])} if row else None
    def require(self,kind,ident):
        r=self.get(kind,ident)
        if not r: raise NotFoundError(f"{kind} not found: {ident}")
        return r
    def list(self,kind=None,limit=500):
        with self.connect() as db:
            rows=db.execute("SELECT * FROM objects WHERE kind=? ORDER BY updated DESC LIMIT ?" if kind else "SELECT * FROM objects ORDER BY updated DESC LIMIT ?", ((kind,limit) if kind else (limit,))).fetchall()
        return [{"kind":r["kind"],"id":r["id"],"version":int(r["version"]),"payload":json.loads(r["payload"])} for r in rows]
    def delete(self,kind,ident):
        with self._lock,self.connect() as db: n=db.execute("DELETE FROM objects WHERE kind=? AND id=?",(kind,ident)).rowcount; self._emit(db,f"{kind}.deleted",{"id":ident}); return bool(n)
    def events(self,since=0,limit=200):
        with self.connect() as db: rows=db.execute("SELECT * FROM events WHERE seq>? ORDER BY seq ASC LIMIT ?",(int(since),int(limit))).fetchall()
        return [{"seq":int(r["seq"]),"ts":float(r["ts"]),"kind":r["kind"],"payload":json.loads(r["payload"])} for r in rows]
    def snapshot(self,label=""):
        sid=str(uuid.uuid4())
        with self._lock,self.connect() as db: db.execute("INSERT INTO snapshots(snapshot_id,label,created_at,payload) VALUES(?,?,?,?)",(sid,label,time.time(),_j({"objects":self.list(limit=10000)}))); self._emit(db,"snapshot.created",{"snapshot_id":sid})
        return {"snapshot_id":sid,"label":label}
    def restore(self,snapshot_id):
        with self.connect() as db: row=db.execute("SELECT * FROM snapshots WHERE snapshot_id=?",(snapshot_id,)).fetchone()
        if not row: raise NotFoundError(snapshot_id)
        objs=json.loads(row["payload"]).get("objects") or []
        with self._lock,self.connect() as db:
            db.execute("DELETE FROM objects")
            for o in objs: db.execute("INSERT INTO objects(kind,id,version,payload,updated) VALUES(?,?,?,?,?)",(o["kind"],o["id"],int(o.get("version",1)),_j(o.get("payload") or {}),time.time()))
            self._emit(db,"snapshot.restored",{"snapshot_id":snapshot_id})
        return {"ok":True,"snapshot_id":snapshot_id,"restored":len(objs)}
    def metrics(self):
        with self.connect() as db: return {"devices":int(db.execute("SELECT COUNT(*) c FROM objects WHERE kind='device'").fetchone()["c"]),"policies":int(db.execute("SELECT COUNT(*) c FROM objects WHERE kind='policy'").fetchone()["c"]),"events":int(db.execute("SELECT COUNT(*) c FROM events").fetchone()["c"])}
