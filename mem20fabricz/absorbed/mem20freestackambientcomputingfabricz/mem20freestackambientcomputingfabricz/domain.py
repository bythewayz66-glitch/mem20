"""Free-stack ambient computing fabric: durable heterogeneous nodes/devices,
atomic versioned reservations with release/expiry/conflict handling, discovery
and allocation across device classes, roaming/disconnection transitions.

Legacy API preserved:
  pool_resources(nodes), discover_services(fabric, capability), allocate(fabric, request),
  fabric_health(fabric), ambient_score(fabric)
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


def pool_resources(nodes):
    nodes = list(nodes or [])
    total_cpu = sum(float(n.get("cpu", 0) or 0) for n in nodes)
    total_mem = sum(float(n.get("memory", 0) or 0) for n in nodes)
    total_storage = sum(float(n.get("storage", 0) or 0) for n in nodes)
    return {"cpu": round(total_cpu, 6), "memory": round(total_mem, 6), "storage": round(total_storage, 6), "nodes": len(nodes)}


def discover_services(fabric, capability):
    cap = str(capability)
    services = list((fabric or {}).get("services", []) or [])
    return [s for s in services if cap in (s.get("capabilities", []) or []) or cap == s.get("type")]


def allocate(fabric, request):
    """Legacy stateless allocation on an in-memory fabric dict."""
    fabric = fabric if isinstance(fabric, dict) else {}
    pool = dict(fabric.get("pool") or pool_resources(fabric.get("nodes") or []))
    req_cpu = float((request or {}).get("cpu", 0) or 0)
    req_mem = float((request or {}).get("memory", 0) or 0)
    req_storage = float((request or {}).get("storage", 0) or 0)
    if pool.get("cpu", 0) >= req_cpu and pool.get("memory", 0) >= req_mem and pool.get("storage", 0) >= req_storage:
        pool["cpu"] = round(pool.get("cpu", 0) - req_cpu, 6)
        pool["memory"] = round(pool.get("memory", 0) - req_mem, 6)
        pool["storage"] = round(pool.get("storage", 0) - req_storage, 6)
        fabric["pool"] = pool
        return {"allocated": True, "remaining": dict(pool)}
    return {"allocated": False, "remaining": dict(pool), "reason": "insufficient_resources"}


def fabric_health(fabric):
    nodes = list((fabric or {}).get("nodes", []) or [])
    if not nodes:
        return {"health": 0.0, "total": 0, "online": 0}
    online = sum(1 for n in nodes if n.get("status") in ("online", "ready", "roaming"))
    return {"total": len(nodes), "online": online, "health": round(online / len(nodes), 4)}


def ambient_score(fabric):
    pool = (fabric or {}).get("pool") or {}
    total = float((fabric or {}).get("total_cpu") or pool.get("cpu", 0) or 1)
    return round(float(pool.get("cpu", 0) or 0) / max(1.0, total), 4)


# ---- durable fabric ----

class AllocationConflict(Exception):
    pass


class FabricStore:
    DEVICE_CLASSES = {"desktop", "mobile", "home", "vehicle", "headset", "edge", "server", "unknown"}

    def __init__(self, db_path: str):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init()

    def _connect(self):
        db = sqlite3.connect(self.db_path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA busy_timeout=15000")
        return db

    def _j(self, o): return json.dumps(o, sort_keys=True, default=str)
    def _jl(self, s): return json.loads(s) if s else {}

    def _init(self):
        with self._connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS nodes(
              node_id TEXT PRIMARY KEY, version INTEGER, device_class TEXT, status TEXT,
              capabilities TEXT, resources TEXT, location TEXT, updated_at REAL, last_seen REAL
            );
            CREATE TABLE IF NOT EXISTS services(
              service_id TEXT PRIMARY KEY, capabilities TEXT, device_classes TEXT, node_id TEXT, status TEXT
            );
            CREATE TABLE IF NOT EXISTS reservations(
              reservation_id TEXT PRIMARY KEY, node_id TEXT, request TEXT, status TEXT,
              version INTEGER, created_at REAL, expires_at REAL, released_at REAL, owner TEXT, idem_key TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_res_node ON reservations(node_id, status);
            CREATE INDEX IF NOT EXISTS idx_res_idem ON reservations(idem_key);
            """)

    def upsert_node(self, node: Mapping[str, Any], expected_version: Optional[int] = None) -> Dict[str, Any]:
        n = dict(node or {})
        nid = str(n.get("node_id") or n.get("id") or f"node-{uuid.uuid4().hex[:8]}")
        dclass = str(n.get("device_class") or n.get("class") or "unknown")
        if dclass not in self.DEVICE_CLASSES:
            self.DEVICE_CLASSES.add(dclass)
        now = time.time()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute("SELECT version,status FROM nodes WHERE node_id=?", (nid,)).fetchone()
                cur = int(row["version"]) if row else 0
                if expected_version is not None and int(expected_version) != cur:
                    raise AllocationConflict(f"node version conflict {nid}: expected {expected_version}, actual {cur}")
                status = str(n.get("status") or (row["status"] if row else "online"))
                ver = cur + 1
                resources = {"cpu": float(n.get("cpu", 0) or 0), "memory": float(n.get("memory", 0) or 0), "storage": float(n.get("storage", 0) or 0), "gpu": float(n.get("gpu", 0) or 0)}
                caps = list(n.get("capabilities") or [])
                db.execute(
                    "INSERT INTO nodes(node_id,version,device_class,status,capabilities,resources,location,updated_at,last_seen) VALUES(?,?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(node_id) DO UPDATE SET version=excluded.version,device_class=excluded.device_class,status=excluded.status,capabilities=excluded.capabilities,resources=excluded.resources,location=excluded.location,updated_at=excluded.updated_at,last_seen=excluded.last_seen",
                    (nid, ver, dclass, status, self._j(caps), self._j(resources), self._j(n.get("location") or {}), now, now),
                )
                for s in (n.get("services") or []):
                    if isinstance(s, Mapping):
                        sid = str(s.get("service_id") or s.get("id") or f"svc-{uuid.uuid4().hex[:8]}")
                        db.execute("INSERT OR REPLACE INTO services(service_id,capabilities,device_classes,node_id,status) VALUES(?,?,?,?,?)",
                                   (sid, self._j(list(s.get("capabilities") or [])), self._j(list(s.get("device_classes") or [dclass])), nid, str(s.get("status") or "online")))
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK"); raise
        return self.get_node(nid)  # type: ignore

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM nodes WHERE node_id=?", (node_id,)).fetchone()
        if not row: return None
        return {"node_id": row["node_id"], "version": int(row["version"]), "device_class": row["device_class"], "status": row["status"], "capabilities": self._jl(row["capabilities"]), "resources": self._jl(row["resources"]), "location": self._jl(row["location"]), "updated_at": float(row["updated_at"]), "last_seen": float(row["last_seen"])}

    def list_nodes(self, device_class: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        q = "SELECT node_id FROM nodes WHERE 1=1"; args = []
        if device_class: q += " AND device_class=?"; args.append(device_class)
        if status: q += " AND status=?"; args.append(status)
        with self._connect() as db:
            ids = [r["node_id"] for r in db.execute(q, args).fetchall()]
        return [self.get_node(i) for i in ids if self.get_node(i)]

    def discover(self, capability: Optional[str] = None, device_class: Optional[str] = None, include_roaming: bool = True) -> List[Dict[str, Any]]:
        statuses = ("online", "ready") + (("roaming",) if include_roaming else ())
        nodes = []
        for n in self.list_nodes(device_class=device_class):
            if not n or n["status"] not in statuses: continue
            if capability and capability not in (n.get("capabilities") or []):
                # also check services
                with self._connect() as db:
                    svc = db.execute("SELECT 1 FROM services WHERE node_id=? AND status='online' AND capabilities LIKE ?", (n["node_id"], f'%"{capability}"%')).fetchone()
                if not svc: continue
            nodes.append(n)
        return nodes

    def _active_reserved(self, db, node_id: str, now: float) -> Dict[str, float]:
        rows = db.execute("SELECT request FROM reservations WHERE node_id=? AND status='active' AND expires_at>?", (node_id, now)).fetchall()
        used = {"cpu": 0.0, "memory": 0.0, "storage": 0.0, "gpu": 0.0}
        for r in rows:
            req = self._jl(r["request"])
            for k in used: used[k] += float(req.get(k, 0) or 0)
        return used

    def reserve(self, request: Mapping[str, Any], owner: str = "caller", lease_s: float = 60.0, idem_key: Optional[str] = None, device_class: Optional[str] = None, capability: Optional[str] = None, node_id: Optional[str] = None) -> Dict[str, Any]:
        req = {k: float((request or {}).get(k, 0) or 0) for k in ("cpu", "memory", "storage", "gpu")}
        now = time.time(); expires = now + max(0.001, float(lease_s))
        rid = f"res-{uuid.uuid4().hex[:16]}"
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                if idem_key:
                    ex = db.execute("SELECT reservation_id,status FROM reservations WHERE idem_key=? ORDER BY created_at DESC LIMIT 1", (str(idem_key),)).fetchone()
                    if ex:
                        db.execute("COMMIT")
                        return self.get_reservation(ex["reservation_id"]) | {"idempotent_replay": True}
                candidates = [self.get_node(node_id)] if node_id else self.discover(capability=capability, device_class=device_class)
                candidates = [c for c in candidates if c and c.get("status") in ("online", "ready", "roaming")]
                chosen = None
                for c in candidates:
                    used = self._active_reserved(db, c["node_id"], now)
                    res = c.get("resources") or {}
                    ok = all(float(res.get(k, 0) or 0) - float(used.get(k, 0) or 0) >= req.get(k, 0) - 1e-9 for k in req)
                    if ok:
                        chosen = c; break
                if not chosen:
                    db.execute("COMMIT")
                    return {"ok": False, "allocated": False, "reservation_id": None, "reason": "no_capacity", "request": req, "device_class": device_class, "capability": capability}
                db.execute("INSERT INTO reservations(reservation_id,node_id,request,status,version,created_at,expires_at,released_at,owner,idem_key) VALUES(?,?,?,?,?,?,?,?,?,?)",
                           (rid, chosen["node_id"], self._j(req), "active", 1, now, expires, None, owner, str(idem_key) if idem_key else None))
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK"); raise
        out = self.get_reservation(rid)
        out.update({"ok": True, "allocated": True, "remaining_hint": "query node availability for exact remaining"})
        return out

    def release(self, reservation_id: str, expected_version: Optional[int] = None) -> Dict[str, Any]:
        now = time.time()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute("SELECT version,status FROM reservations WHERE reservation_id=?", (reservation_id,)).fetchone()
                if not row:
                    db.execute("COMMIT"); return {"ok": False, "error": "not_found"}
                if expected_version is not None and int(row["version"]) != int(expected_version):
                    raise AllocationConflict(f"reservation version conflict")
                ver = int(row["version"]) + 1
                db.execute("UPDATE reservations SET status='released', version=?, released_at=? WHERE reservation_id=?", (ver, now, reservation_id))
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK"); raise
        return self.get_reservation(reservation_id) | {"ok": True}

    def expire_leases(self) -> Dict[str, Any]:
        now = time.time()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            cur = db.execute("UPDATE reservations SET status='expired', released_at=? WHERE status='active' AND expires_at<=?", (now, now))
            n = cur.rowcount
            db.execute("COMMIT")
        return {"ok": True, "expired": int(n)}

    def mark_node_status(self, node_id: str, status: str) -> Dict[str, Any]:
        now = time.time()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE nodes SET status=?, updated_at=? WHERE node_id=?", (str(status), now, node_id))
            if status in ("lost", "offline"):
                db.execute("UPDATE reservations SET status='orphaned', released_at=? WHERE node_id=? AND status='active'", (now, node_id))
            db.execute("COMMIT")
        return {"ok": True, "node": self.get_node(node_id)}

    def get_reservation(self, reservation_id: str) -> Dict[str, Any]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM reservations WHERE reservation_id=?", (reservation_id,)).fetchone()
        if not row: return {"ok": False, "error": "not_found"}
        return {"ok": True, "reservation_id": row["reservation_id"], "node_id": row["node_id"], "request": self._jl(row["request"]), "status": row["status"], "version": int(row["version"]), "created_at": float(row["created_at"]), "expires_at": float(row["expires_at"]), "released_at": float(row["released_at"]) if row["released_at"] else None, "owner": row["owner"], "idem_key": row["idem_key"]}

    def fabric_snapshot(self) -> Dict[str, Any]:
        nodes = self.list_nodes()
        return {"nodes": nodes, "pool": pool_resources([n.get("resources") or {} for n in nodes]), "health": fabric_health({"nodes": [{"status": n.get("status")} for n in nodes]}), "device_classes": sorted({n.get("device_class") for n in nodes if n})}
