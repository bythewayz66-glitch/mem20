"""Execution digital twin: process mirror, simulation, prediction.

Legacy API preserved (dict-based, in-memory):
  create_twin(process), sync_twin(twin, real_state), simulate(twin, actions),
  predict_outcome(twin, action), drift(twin, real_state)

Durable telemetry twin API (SQLite-backed):
  DurableTelemetryTwin(db_path) persists twin identity, versioned state,
  telemetry observations, timestamps, and checkpoints; reconciles duplicate,
  delayed, missing, and out-of-order events; tracks drift over time and
  distinguishes observed vs predicted/counterfactual state.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


# ---- legacy-compatible API ----

def create_twin(process):
    return {
        "id": process.get("id"),
        "state": dict(process.get("state", {}) or {}),
        "metrics": dict(process.get("metrics", {}) or {}),
        "synced_at": 0,
        "version": 0,
        "mode": "observed",
        "history": [],
    }


def sync_twin(twin, real_state):
    twin["state"] = dict(real_state or {})
    twin["synced_at"] = time.time()
    twin["version"] = int(twin.get("version", 0) or 0) + 1
    twin.setdefault("history", []).append({"ts": twin["synced_at"], "state": dict(twin["state"]), "kind": "observed"})
    return twin


def simulate(twin, actions):
    results = []
    state = dict(twin.get("state", {}) or {})
    for a in actions or []:
        state.update(dict((a or {}).get("effect", {}) or {}))
        results.append({"action": (a or {}).get("name"), "state": dict(state), "mode": "predicted"})
    return results


def predict_outcome(twin, action):
    base = (twin.get("metrics", {}) or {}).get("success_rate", 0.5)
    effect = (action or {}).get("impact", 0.0)
    return round(min(1.0, max(0.0, float(base) + float(effect))), 4)


def drift(twin, real_state):
    diffs = {}
    tstate = dict(twin.get("state", {}) or {})
    rstate = dict(real_state or {})
    for k in set(tstate) | set(rstate):
        if tstate.get(k) != rstate.get(k):
            diffs[k] = {"twin": tstate.get(k), "real": rstate.get(k)}
    return diffs


# ---- durable telemetry twin ----

class TelemetryConflict(Exception):
    pass


class DurableTelemetryTwin:
    def __init__(self, db_path: str):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init()

    def _connect(self):
        db = sqlite3.connect(self.db_path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def _init(self):
        with self._connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS twins(
              twin_id TEXT PRIMARY KEY, process_id TEXT, version INTEGER, observed_state TEXT,
              predicted_state TEXT, metrics TEXT, created_at REAL, updated_at REAL,
              last_observed_ts REAL, last_event_ts REAL, checkpoint_seq INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS observations(
              twin_id TEXT, observation_id TEXT, source_seq INTEGER, event_ts REAL, ingest_ts REAL,
              kind TEXT, payload TEXT, state_after TEXT, version INTEGER, status TEXT,
              PRIMARY KEY(twin_id, observation_id)
            );
            CREATE TABLE IF NOT EXISTS checkpoints(
              twin_id TEXT, checkpoint_id TEXT PRIMARY KEY, seq INTEGER, ts REAL, label TEXT,
              version INTEGER, observed_state TEXT, predicted_state TEXT
            );
            CREATE TABLE IF NOT EXISTS drift_log(
              id INTEGER PRIMARY KEY AUTOINCREMENT, twin_id TEXT, ts REAL, version INTEGER,
              observed_state TEXT, predicted_state TEXT, diff TEXT
            );
            """)

    def _j(self, o):
        return json.dumps(o, sort_keys=True, default=str)

    def _jl(self, s):
        return json.loads(s) if s else {}

    def register(self, process: Mapping[str, Any], twin_id: Optional[str] = None) -> Dict[str, Any]:
        tid = str(twin_id or process.get("twin_id") or process.get("id") or f"twin-{uuid.uuid4().hex[:12]}")
        now = time.time()
        state = dict(process.get("state", {}) or {})
        metrics = dict(process.get("metrics", {}) or {})
        with self._lock, self._connect() as db:
            row = db.execute("SELECT twin_id, version FROM twins WHERE twin_id=?", (tid,)).fetchone()
            if row:
                return self.get(tid)  # type: ignore
            db.execute(
                "INSERT INTO twins(twin_id,process_id,version,observed_state,predicted_state,metrics,created_at,updated_at,last_observed_ts,last_event_ts,checkpoint_seq) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (tid, str(process.get("id") or tid), 0, self._j(state), self._j(state), self._j(metrics), now, now, 0.0, 0.0, 0),
            )
        return self.get(tid)  # type: ignore

    def get(self, twin_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM twins WHERE twin_id=?", (twin_id,)).fetchone()
        if not row:
            return None
        return {
            "twin_id": row["twin_id"],
            "process_id": row["process_id"],
            "version": int(row["version"]),
            "observed_state": self._jl(row["observed_state"]),
            "predicted_state": self._jl(row["predicted_state"]),
            "metrics": self._jl(row["metrics"]),
            "created_at": float(row["created_at"]),
            "updated_at": float(row["updated_at"]),
            "last_observed_ts": float(row["last_observed_ts"] or 0),
            "last_event_ts": float(row["last_event_ts"] or 0),
            "checkpoint_seq": int(row["checkpoint_seq"] or 0),
        }

    def require(self, twin_id: str) -> Dict[str, Any]:
        t = self.get(twin_id)
        if not t:
            raise KeyError(f"twin not found: {twin_id}")
        return t

    def _checkpoint(self, db, twin: Mapping[str, Any], label: str = "auto"):
        seq = int(twin.get("checkpoint_seq", 0) or 0) + 1
        cid = f"{twin['twin_id']}:cp:{seq}:{uuid.uuid4().hex[:8]}"
        db.execute(
            "INSERT INTO checkpoints(twin_id,checkpoint_id,seq,ts,label,version,observed_state,predicted_state) VALUES(?,?,?,?,?,?,?,?)",
            (twin["twin_id"], cid, seq, time.time(), label, int(twin["version"]), self._j(twin["observed_state"]), self._j(twin["predicted_state"])),
        )
        db.execute("UPDATE twins SET checkpoint_seq=? WHERE twin_id=?", (seq, twin["twin_id"]))
        return cid, seq

    def ingest(self, twin_id: str, observation: Mapping[str, Any], stale_after_s: Optional[float] = None) -> Dict[str, Any]:
        """Ingest telemetry observation. Handles duplicate, delayed, missing-seq, out-of-order.
        observation: {observation_id?, source_seq?, event_ts, state|payload, kind?}
        """
        obs = dict(observation or {})
        obs_id = str(obs.get("observation_id") or obs.get("id") or f"obs-{uuid.uuid4().hex}")
        source_seq = int(obs.get("source_seq", obs.get("seq", -1)) or -1)
        event_ts = float(obs.get("event_ts", obs.get("ts", obs.get("timestamp", time.time()))) or time.time())
        kind = str(obs.get("kind") or "telemetry")
        payload = dict(obs.get("state") or obs.get("payload") or obs)
        # remove envelope keys from payload if state was nested
        if "state" in obs and isinstance(obs["state"], dict):
            payload = dict(obs["state"])
        ingest_ts = time.time()
        with self._lock, self._connect() as db:
            twin_row = db.execute("SELECT * FROM twins WHERE twin_id=?", (twin_id,)).fetchone()
            if not twin_row:
                raise KeyError(f"twin not found: {twin_id}")
            dup = db.execute("SELECT 1 FROM observations WHERE twin_id=? AND observation_id=?", (twin_id, obs_id)).fetchone()
            if dup:
                return {"ok": True, "twin_id": twin_id, "observation_id": obs_id, "status": "duplicate", "applied": False, "version": int(twin_row["version"])}
            last_event_ts = float(twin_row["last_event_ts"] or 0)
            last_observed_ts = float(twin_row["last_observed_ts"] or 0)
            stale = bool(stale_after_s is not None and last_observed_ts > 0 and (ingest_ts - last_observed_ts) > float(stale_after_s))
            out_of_order = event_ts < last_event_ts
            delayed = out_of_order or (ingest_ts - event_ts > max(5.0, float(stale_after_s or 30.0)))
            missing_seq = False
            if source_seq >= 0:
                prev = db.execute("SELECT MAX(source_seq) m FROM observations WHERE twin_id=? AND source_seq>=0", (twin_id,)).fetchone()
                prev_m = int(prev["m"]) if prev and prev["m"] is not None else -1
                missing_seq = prev_m >= 0 and source_seq > prev_m + 1
            observed = self._jl(twin_row["observed_state"])
            predicted = self._jl(twin_row["predicted_state"])
            status = "applied"
            applied = True
            version = int(twin_row["version"])
            # reconciliation: out-of-order/delayed observations are recorded but do not regress observed state by default
            if out_of_order and kind != "correction":
                status = "recorded_out_of_order"
                applied = False
                state_after = dict(observed)
            else:
                # merge/correct observed state
                state_after = dict(observed)
                state_after.update(payload)
                observed = state_after
                version += 1
                diff = drift({"state": predicted}, observed)
                db.execute("INSERT INTO drift_log(twin_id,ts,version,observed_state,predicted_state,diff) VALUES(?,?,?,?,?,?)",
                           (twin_id, ingest_ts, version, self._j(observed), self._j(predicted), self._j(diff)))
                db.execute(
                    "UPDATE twins SET version=?, observed_state=?, updated_at=?, last_observed_ts=?, last_event_ts=? WHERE twin_id=?",
                    (version, self._j(observed), ingest_ts, event_ts, max(last_event_ts, event_ts), twin_id),
                )
            if stale:
                status = status + "+stale_gap_detected"
            if missing_seq:
                status = status + "+missing_seq_detected"
            if delayed and "delayed" not in status:
                status = status + "+delayed"
            db.execute(
                "INSERT INTO observations(twin_id,observation_id,source_seq,event_ts,ingest_ts,kind,payload,state_after,version,status) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (twin_id, obs_id, source_seq, event_ts, ingest_ts, kind, self._j(payload), self._j(state_after), version, status),
            )
            twin = self.require(twin_id)
            if version > 0 and version % 5 == 0 and applied:
                self._checkpoint(db, twin, label=f"v{version}")
        return {
            "ok": True, "twin_id": twin_id, "observation_id": obs_id, "status": status,
            "applied": applied, "version": version, "event_ts": event_ts, "ingest_ts": ingest_ts,
            "out_of_order": out_of_order, "delayed": delayed, "missing_seq": missing_seq, "stale_gap": stale,
        }

    def predict(self, twin_id: str, actions: Sequence[Mapping[str, Any]] = None, action: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        with self._lock, self._connect() as db:
            twin = self.require(twin_id)
            predicted = dict(twin["observed_state"])
            steps = []
            for a in (actions or ([action] if action else [])):
                if not a:
                    continue
                predicted.update(dict(a.get("effect", {}) or {}))
                steps.append({"action": a.get("name"), "state": dict(predicted), "mode": "predicted_counterfactual"})
            db.execute("UPDATE twins SET predicted_state=?, updated_at=? WHERE twin_id=?", (self._j(predicted), time.time(), twin_id))
        twin = self.require(twin_id)
        outcome = predict_outcome({"metrics": twin["metrics"]}, action or (actions[0] if actions else {}))
        return {"ok": True, "twin_id": twin_id, "observed_state": twin["observed_state"], "predicted_state": twin["predicted_state"], "prediction_steps": steps, "predicted_outcome": outcome, "mode": "predicted"}

    def drift_report(self, twin_id: str, limit: int = 50) -> Dict[str, Any]:
        twin = self.require(twin_id)
        with self._connect() as db:
            rows = db.execute("SELECT * FROM drift_log WHERE twin_id=? ORDER BY id DESC LIMIT ?", (twin_id, limit)).fetchall()
        history = [{"ts": float(r["ts"]), "version": int(r["version"]), "diff": self._jl(r["diff"])} for r in reversed(rows)]
        current = drift({"state": twin["predicted_state"]}, twin["observed_state"])
        return {"ok": True, "twin_id": twin_id, "current_drift": current, "observed_state": twin["observed_state"], "predicted_state": twin["predicted_state"], "history": history}

    def replay(self, twin_id: str, since_ts: float = 0.0) -> Dict[str, Any]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM observations WHERE twin_id=? AND event_ts>=? ORDER BY event_ts ASC, ingest_ts ASC", (twin_id, float(since_ts))).fetchall()
        events = [{"observation_id": r["observation_id"], "source_seq": int(r["source_seq"]), "event_ts": float(r["event_ts"]), "ingest_ts": float(r["ingest_ts"]), "kind": r["kind"], "status": r["status"], "version": int(r["version"])} for r in rows]
        return {"ok": True, "twin_id": twin_id, "events": events, "count": len(events)}

    def checkpoint(self, twin_id: str, label: str = "manual") -> Dict[str, Any]:
        with self._lock, self._connect() as db:
            twin = self.require(twin_id)
            cid, seq = self._checkpoint(db, twin, label=label)
        return {"ok": True, "twin_id": twin_id, "checkpoint_id": cid, "seq": seq}

    def status(self, twin_id: str) -> Dict[str, Any]:
        twin = self.require(twin_id)
        with self._connect() as db:
            obs = db.execute("SELECT COUNT(*) c, SUM(CASE WHEN status LIKE '%out_of_order%' THEN 1 ELSE 0 END) ooo, SUM(CASE WHEN status LIKE '%duplicate%' THEN 1 ELSE 0 END) dup, SUM(CASE WHEN status LIKE '%stale%' THEN 1 ELSE 0 END) stale FROM observations WHERE twin_id=?", (twin_id,)).fetchone()
            cps = db.execute("SELECT COUNT(*) c FROM checkpoints WHERE twin_id=?", (twin_id,)).fetchone()
        return {
            "ok": True, "twin": twin,
            "observations": int(obs["c"] or 0), "out_of_order_recorded": int(obs["ooo"] or 0),
            "duplicates": int(obs["dup"] or 0), "stale_gaps": int(obs["stale"] or 0),
            "checkpoints": int(cps["c"] or 0),
        }
