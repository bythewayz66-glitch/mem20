"""mem20labz runtime/service: durable lab sessions, probes, and orchestration."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from . import MEMBERS, __version__
from . import domain
from . import ecosystem


DEFAULT_DB = Path(os.environ.get("MEM20_LABZ_DB", str(Path.home() / ".mem20" / "mem20labz.sqlite3")))


class LabStore:
    def __init__(self, path: str | Path | None = None):
        self.path = str(path or DEFAULT_DB)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init()

    def _connect(self):
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._lock, self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=NORMAL")
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                  id TEXT PRIMARY KEY,
                  kind TEXT NOT NULL,
                  target TEXT,
                  status TEXT NOT NULL,
                  payload TEXT NOT NULL,
                  result TEXT,
                  created_at REAL NOT NULL,
                  updated_at REAL NOT NULL
                )
                """
            )
            db.execute("CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at DESC)")
            db.commit()

    def record_run(self, run_id: str, kind: str, target: str | None, payload: Mapping[str, Any], result: Mapping[str, Any], status: str = "completed"):
        now = time.time()
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO runs(id,kind,target,status,payload,result,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                (run_id, kind, target, status, json.dumps(dict(payload), sort_keys=True), json.dumps(dict(result), sort_keys=True, default=str), now, now),
            )
            db.commit()

    def list_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock, self._connect() as db:
            rows = db.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (max(1, min(500, int(limit))),)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            for k in ("payload", "result"):
                try:
                    d[k] = json.loads(d[k]) if d.get(k) else None
                except Exception:
                    pass
            out.append(d)
        return out

    def stats(self) -> Dict[str, Any]:
        with self._lock, self._connect() as db:
            total = db.execute("SELECT COUNT(*) c FROM runs").fetchone()["c"]
            kinds = db.execute("SELECT kind, COUNT(*) c FROM runs GROUP BY kind").fetchall()
        return {"db_path": self.path, "total_runs": total, "by_kind": {r["kind"]: r["c"] for r in kinds}}


class LabRuntime:
    def __init__(self, db_path: str | Path | None = None):
        self.store = LabStore(db_path)

    def status(self) -> Dict[str, Any]:
        return {
            "ok": True,
            "runtime": "mem20labz",
            "version": __version__,
            "members": list(MEMBERS),
            "member_count": len(MEMBERS),
            "store": self.store.stats(),
            "ts": time.time(),
        }

    def registry(self) -> Dict[str, Any]:
        return domain.registry()

    def probe(self, member: Optional[str] = None) -> Dict[str, Any]:
        run_id = domain._run_id("probe")
        if member:
            result = domain.probe_member(member)
            self.store.record_run(run_id, "probe", member, {"member": member}, result, "completed" if result.get("ok") else "failed")
            return {"run_id": run_id, **result}
        result = domain.probe_all()
        self.store.record_run(run_id, "probe_all", None, {"members": list(MEMBERS)}, result, "completed" if result.get("ok") else "degraded")
        return {"run_id": run_id, **result}

    def simulate(self, member: Optional[str] = None, payload: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        payload = dict(payload or {})
        run_id = domain._run_id("simulate")
        if member:
            result = domain.run_member_simulation(member, payload)
            self.store.record_run(run_id, "simulate", member, payload, result, "completed" if result.get("ok") else "failed")
            return {"run_id": run_id, **result}
        results = [domain.run_member_simulation(m, payload) for m in MEMBERS]
        agg = domain.aggregate(results)
        result = {"ok": agg["failed"] == 0, "results": results, "aggregate": agg}
        self.store.record_run(run_id, "simulate_all", None, payload, result, "completed" if result.get("ok") else "degraded")
        return {"run_id": run_id, **result}

    def signals(self) -> Dict[str, Any]:
        run_id = domain._run_id("signals")
        result = ecosystem.lab_signals()
        self.store.record_run(run_id, "signals", None, {}, result, "completed" if result.get("ok") else "degraded")
        return {"run_id": run_id, **result}

    def history(self, limit: int = 50) -> Dict[str, Any]:
        return {"ok": True, "runs": self.store.list_runs(limit)}
