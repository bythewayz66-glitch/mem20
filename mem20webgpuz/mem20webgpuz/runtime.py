"""mem20webgpuz runtime — durable job execution over the domain engine.

The runtime is the stateful half of the subsystem. It owns:

* a SQLite WAL store (jobs, events, feedback, cache, resources, LWW key/value)
* idempotent job creation, so a replayed request returns the first result
* bounded retries with backoff, cancellation, timeouts and a concurrency quota
* deterministic recovery of jobs left ``queued``/``running`` by a crash
* metrics with a Prometheus text exposition

It deliberately does not re-implement the domain: every job funnels through
``webgpu.run_domain`` so the API, CLI and SDK all return the same shape.
"""

from __future__ import annotations

import contextlib
import json
import math
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

from mem20core.mem20core.core import canonical, redact, stable_hash

from . import webgpu
from .config import WebGPUConfig
from .errors import (
    JobCancelledError,
    JobNotFoundError,
    QuotaExceededError,
    RetryPolicy,
    TransientError,
    ValidationError,
    WebGPUError,
    idempotency_key,
)

__all__ = ["StateStore", "Metrics", "Runtime", "JobResult", "SCHEMA_VERSION"]

SCHEMA_VERSION = "1.0"

_TERMINAL = {"succeeded", "failed", "cancelled"}


def _now() -> float:
    return time.time()


@dataclass(frozen=True)
class JobResult:
    """The outcome of one job, as returned by every surface."""

    job_id: str
    state: str
    roadmap_id: int
    title: str
    result: dict[str, Any] | None
    error: str | None
    attempts: int
    cache_hit: bool
    recovered: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "state": self.state,
            "roadmap_id": self.roadmap_id,
            "title": self.title,
            "result": self.result,
            "error": self.error,
            "attempts": self.attempts,
            "cache_hit": self.cache_hit,
            "recovered": self.recovered,
        }


class StateStore:
    """SQLite WAL persistence for jobs, events, feedback, cache and resources."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    @contextlib.contextmanager
    def conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init(self) -> None:
        with self.conn() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS jobs(
                    id TEXT PRIMARY KEY, idem TEXT UNIQUE, state TEXT,
                    request TEXT, result TEXT, error TEXT, attempts INTEGER,
                    created REAL, updated REAL);
                CREATE TABLE IF NOT EXISTS events(
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, kind TEXT,
                    job_id TEXT, payload TEXT);
                CREATE TABLE IF NOT EXISTS feedback(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, signal TEXT,
                    value REAL, note TEXT);
                CREATE TABLE IF NOT EXISTS cache(k TEXT PRIMARY KEY, ts REAL, value TEXT);
                CREATE TABLE IF NOT EXISTS kv(
                    k TEXT PRIMARY KEY, ts REAL, node TEXT, value TEXT,
                    tombstone INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS resources(
                    id TEXT PRIMARY KEY, version INTEGER, created REAL,
                    updated REAL, body TEXT);
                """
            )

    # -- events ------------------------------------------------------------
    def emit(self, kind: str, job_id: str | None = None, payload: Any = None) -> None:
        safe = redact(payload if payload is not None else {})
        with self.conn() as conn:
            conn.execute(
                "INSERT INTO events(ts,kind,job_id,payload) VALUES(?,?,?,?)",
                (_now(), kind, job_id, canonical(safe)),
            )

    def events(self, after: int = 0, limit: int = 500) -> list[dict[str, Any]]:
        with self.conn() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE seq>? ORDER BY seq LIMIT ?",
                (int(after), int(limit)),
            ).fetchall()
        return [dict(r) for r in rows]

    # -- jobs --------------------------------------------------------------
    def create_job(self, request: Mapping[str, Any], idem: str | None = None) -> tuple[dict[str, Any], bool]:
        key = idem or idempotency_key(dict(request))
        with self.conn() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE idem=?", (key,)).fetchone()
            if row:
                return dict(row), False
            jid = str(uuid.uuid4())
            ts = _now()
            conn.execute(
                "INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?)",
                (jid, key, "queued", canonical(redact(dict(request))), None, None, 0, ts, ts),
            )
        self.emit("job.queued", jid, dict(request))
        job = self.get_job(jid)
        assert job is not None
        return job, True

    def get_job(self, jid: str) -> dict[str, Any] | None:
        with self.conn() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
        return dict(row) if row else None

    def require_job(self, jid: str) -> dict[str, Any]:
        job = self.get_job(jid)
        if job is None:
            raise JobNotFoundError("no such job", details={"job_id": jid})
        return job

    def list_jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.conn() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY created DESC LIMIT ?", (int(limit),)
            ).fetchall()
        return [dict(r) for r in rows]

    def update_job(
        self,
        jid: str,
        state: str,
        result: Any = None,
        error: str | None = None,
        attempts: int | None = None,
    ) -> None:
        safe_result = canonical(redact(result)) if result is not None else None
        safe_error = redact(error) if isinstance(error, str) else error
        with self.conn() as conn:
            old = conn.execute("SELECT attempts FROM jobs WHERE id=?", (jid,)).fetchone()
            att = attempts if attempts is not None else (old["attempts"] if old else 0)
            conn.execute(
                "UPDATE jobs SET state=?,result=?,error=?,attempts=?,updated=? WHERE id=?",
                (state, safe_result, safe_error, att, _now(), jid),
            )
        self.emit("job." + state, jid, result if result is not None else {"error": error})

    def cancel(self, jid: str) -> bool:
        job = self.get_job(jid)
        if job is None:
            raise JobNotFoundError("no such job", details={"job_id": jid})
        if job["state"] in _TERMINAL:
            return False
        self.update_job(jid, "cancelled")
        return True

    # -- feedback ----------------------------------------------------------
    def feedback(self, signal: str, value: float, note: str = "") -> None:
        with self.conn() as conn:
            conn.execute(
                "INSERT INTO feedback(ts,signal,value,note) VALUES(?,?,?,?)",
                (_now(), signal, float(value), note),
            )
        self.emit("feedback", None, {"signal": signal, "value": value, "note": note})

    def feedback_bias(self) -> dict[str, float]:
        with self.conn() as conn:
            rows = conn.execute(
                "SELECT signal,AVG(value) v FROM feedback GROUP BY signal"
            ).fetchall()
        return {r["signal"]: float(r["v"]) for r in rows}

    # -- cache -------------------------------------------------------------
    def cache_get(self, key: str, max_age: float = 3600) -> Any | None:
        with self.conn() as conn:
            row = conn.execute("SELECT * FROM cache WHERE k=?", (key,)).fetchone()
        if not row or _now() - row["ts"] > max_age:
            return None
        return json.loads(row["value"])

    def cache_put(self, key: str, value: Any) -> None:
        with self.conn() as conn:
            conn.execute(
                "INSERT INTO cache(k,ts,value) VALUES(?,?,?) "
                "ON CONFLICT(k) DO UPDATE SET ts=excluded.ts,value=excluded.value",
                (key, _now(), canonical(value)),
            )

    # -- LWW sync ----------------------------------------------------------
    def put_lww(
        self, key: str, value: Any, node: str = "local", ts: float | None = None,
        tombstone: bool = False,
    ) -> bool:
        stamp = float(ts if ts is not None else _now())
        with self.conn() as conn:
            old = conn.execute("SELECT ts,node FROM kv WHERE k=?", (key,)).fetchone()
            if old and (old["ts"], old["node"]) >= (stamp, node):
                return False
            conn.execute(
                "INSERT INTO kv(k,ts,node,value,tombstone) VALUES(?,?,?,?,?) "
                "ON CONFLICT(k) DO UPDATE SET ts=excluded.ts,node=excluded.node,"
                "value=excluded.value,tombstone=excluded.tombstone",
                (key, stamp, node, canonical(value), 1 if tombstone else 0),
            )
        self.emit("sync.update", None, {"key": key, "node": node, "ts": stamp})
        return True

    def export_lww(self) -> list[dict[str, Any]]:
        with self.conn() as conn:
            rows = conn.execute("SELECT * FROM kv").fetchall()
        return [dict(r) for r in rows]

    def merge_lww(self, rows: list[Mapping[str, Any]]) -> int:
        merged = 0
        for row in rows:
            value = row["value"]
            if isinstance(value, str):
                value = json.loads(value)
            if self.put_lww(
                row["k"], value, row["node"], row["ts"], bool(row.get("tombstone"))
            ):
                merged += 1
        return merged

    # -- resources ---------------------------------------------------------
    def resource_create(self, body: Any, rid: str | None = None) -> dict[str, Any]:
        ident = rid or str(uuid.uuid4())
        ts = _now()
        with self.conn() as conn:
            conn.execute(
                "INSERT INTO resources(id,version,created,updated,body) VALUES(?,?,?,?,?)",
                (ident, 1, ts, ts, canonical(redact(body))),
            )
        self.emit("resource.created", None, {"id": ident, "version": 1})
        created = self.resource_get(ident)
        assert created is not None
        return created

    def resource_get(self, rid: str) -> dict[str, Any] | None:
        with self.conn() as conn:
            row = conn.execute("SELECT * FROM resources WHERE id=?", (rid,)).fetchone()
        if not row:
            return None
        out = dict(row)
        out["body"] = json.loads(out["body"])
        return out

    def resource_list(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.conn() as conn:
            rows = conn.execute(
                "SELECT * FROM resources ORDER BY updated DESC LIMIT ?", (int(limit),)
            ).fetchall()
        out = []
        for row in rows:
            item = dict(row)
            item["body"] = json.loads(item["body"])
            out.append(item)
        return out

    def resource_update(
        self, rid: str, body: Any, expected_version: int | None = None
    ) -> dict[str, Any]:
        with self.conn() as conn:
            row = conn.execute("SELECT version FROM resources WHERE id=?", (rid,)).fetchone()
            if not row:
                raise JobNotFoundError("no such resource", details={"id": rid})
            if expected_version is not None and int(expected_version) != int(row["version"]):
                raise ValidationError(
                    "resource version conflict",
                    details={"expected": expected_version, "actual": row["version"]},
                )
            version = int(row["version"]) + 1
            conn.execute(
                "UPDATE resources SET version=?,updated=?,body=? WHERE id=?",
                (version, _now(), canonical(redact(body)), rid),
            )
        self.emit("resource.updated", None, {"id": rid, "version": version})
        updated = self.resource_get(rid)
        assert updated is not None
        return updated

    def resource_delete(self, rid: str, expected_version: int | None = None) -> bool:
        with self.conn() as conn:
            row = conn.execute("SELECT version FROM resources WHERE id=?", (rid,)).fetchone()
            if not row:
                return False
            if expected_version is not None and int(expected_version) != int(row["version"]):
                raise ValidationError(
                    "resource version conflict",
                    details={"expected": expected_version, "actual": row["version"]},
                )
            conn.execute("DELETE FROM resources WHERE id=?", (rid,))
        self.emit("resource.deleted", None, {"id": rid})
        return True


class Metrics:
    """Thread-safe counters and a bounded latency reservoir."""

    def __init__(self, reservoir: int = 5000) -> None:
        self._lock = threading.Lock()
        self._counts: dict[str, int] = {}
        self._latencies: list[float] = []
        self._reservoir = reservoir

    def inc(self, key: str, amount: int = 1) -> None:
        with self._lock:
            self._counts[key] = self._counts.get(key, 0) + amount

    def observe(self, value: float) -> None:
        with self._lock:
            self._latencies.append(float(value))
            if len(self._latencies) > self._reservoir:
                self._latencies = self._latencies[-self._reservoir:]

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            latencies = list(self._latencies)
            counts = dict(self._counts)
        return {
            "counts": counts,
            "latency_ms_avg": round(sum(latencies) / len(latencies), 4) if latencies else 0.0,
            "latency_ms_p95": (
                round(sorted(latencies)[max(0, math.ceil(0.95 * len(latencies)) - 1)], 4)
                if latencies else 0.0
            ),
            "samples": len(latencies),
        }

    def prometheus(self) -> str:
        snap = self.snapshot()
        lines = [
            f"mem20webgpuz_{_sanitize(k)} {v}" for k, v in sorted(snap["counts"].items())
        ]
        lines.append(f"mem20webgpuz_latency_ms_avg {snap['latency_ms_avg']}")
        lines.append(f"mem20webgpuz_latency_ms_p95 {snap['latency_ms_p95']}")
        lines.append(f"mem20webgpuz_latency_samples {snap['samples']}")
        return "\n".join(lines) + "\n"


def _sanitize(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)


class Runtime:
    """Executes domain jobs durably, with retries, quotas and recovery."""

    def __init__(
        self,
        config: WebGPUConfig | None = None,
        *,
        roadmap: Mapping[str, Any] | None = None,
        retry_policy: RetryPolicy | None = None,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config or WebGPUConfig.from_env()
        self.roadmap = dict(roadmap) if roadmap is not None else webgpu.load_roadmap()
        self.retry_policy = retry_policy or RetryPolicy()
        self._clock = clock
        self._sleep = sleep
        self.store = StateStore(self.config.data_dir / "webgpuz.sqlite3")
        self.metrics = Metrics()
        self._sem = threading.BoundedSemaphore(self.config.max_concurrent)
        self._cancel: dict[str, bool] = {}
        self._lock = threading.Lock()

    # -- introspection -----------------------------------------------------
    def inspect(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "domain_version": webgpu.DOMAIN_VERSION,
            "roadmap": {
                "global_id": self.roadmap.get("global_id"),
                "title": self.roadmap.get("title"),
                "outcome": self.roadmap.get("outcome"),
            },
            "config": self.config.to_dict(),
            "metrics": self.metrics.snapshot(),
            "retry_policy": self.retry_policy.to_dict(),
        }

    def health(self) -> dict[str, Any]:
        """Liveness: the process is up and the store answers."""
        try:
            self.store.list_jobs(1)
            store_ok = True
        except sqlite3.Error:
            store_ok = False
        return {"ok": store_ok, "roadmap_id": self.roadmap.get("global_id")}

    def readiness(self) -> dict[str, Any]:
        """Readiness: the store is writable and the domain engine is importable."""
        checks: dict[str, bool] = {}
        try:
            self.store.emit("readiness.probe", None, {})
            checks["store_writable"] = True
        except sqlite3.Error:
            checks["store_writable"] = False
        checks["domain_engine"] = callable(webgpu.run_domain)
        return {"ready": all(checks.values()), "checks": checks}

    # -- execution ---------------------------------------------------------
    def run(
        self,
        request: Mapping[str, Any],
        idem: str | None = None,
        *,
        timeout: float | None = None,
    ) -> JobResult:
        """Execute one job. Idempotent on ``idem`` (or a digest of the request)."""
        self._validate_request(request)
        job, created = self.store.create_job(request, idem)
        jid = job["id"]

        if not created and job["state"] == "succeeded" and job["result"]:
            payload = json.loads(job["result"])
            return JobResult(
                job_id=jid, state="succeeded",
                roadmap_id=int(self.roadmap.get("global_id", 0)),
                title=str(self.roadmap.get("title", "")),
                result=payload, error=None, attempts=int(job["attempts"] or 0),
                cache_hit=True,
            )

        with self._lock:
            self._cancel[jid] = False

        acquired = self._sem.acquire(timeout=self.config.queue_timeout)
        if not acquired:
            self.store.update_job(jid, "failed", error="backpressure: queue timeout")
            self.metrics.inc("jobs_rejected")
            raise QuotaExceededError(
                "backpressure: queue timeout",
                details={"queue_timeout": self.config.queue_timeout},
            )

        started = self._clock()
        try:
            if self._is_cancelled(jid):
                raise JobCancelledError("cancelled before start", details={"job_id": jid})
            self.store.update_job(jid, "running", attempts=1)

            cache_key = stable_hash(
                {"rm": self.roadmap.get("global_id"), "request": dict(request)}
            )
            if request.get("cache", True):
                cached = self.store.cache_get(cache_key, float(request.get("cache_ttl", 3600)))
                if cached is not None:
                    self.store.update_job(jid, "succeeded", cached)
                    self.metrics.inc("cache_hit")
                    return JobResult(
                        job_id=jid, state="succeeded",
                        roadmap_id=int(self.roadmap.get("global_id", 0)),
                        title=str(self.roadmap.get("title", "")),
                        result=cached, error=None, attempts=1, cache_hit=True,
                    )

            result = self._execute_with_retries(jid, request, timeout)
            self.store.cache_put(cache_key, result)
            self.store.update_job(jid, "succeeded", result)
            self.metrics.inc("jobs_succeeded")
            self.metrics.observe((self._clock() - started) * 1000.0)
            return JobResult(
                job_id=jid, state="succeeded",
                roadmap_id=int(self.roadmap.get("global_id", 0)),
                title=str(self.roadmap.get("title", "")),
                result=result, error=None, attempts=self._attempts(jid), cache_hit=False,
            )
        except JobCancelledError as exc:
            self.store.update_job(jid, "cancelled", error=str(exc))
            self.metrics.inc("jobs_cancelled")
            raise
        except WebGPUError as exc:
            self.store.update_job(jid, "failed", error=f"{type(exc).__name__}: {exc}")
            self.metrics.inc("jobs_failed")
            raise
        except Exception as exc:  # noqa: BLE001 - recorded, then re-raised
            self.store.update_job(jid, "failed", error=f"{type(exc).__name__}: {exc}")
            self.metrics.inc("jobs_failed")
            raise
        finally:
            self._sem.release()
            with self._lock:
                self._cancel.pop(jid, None)

    def _execute_with_retries(
        self, jid: str, request: Mapping[str, Any], timeout: float | None
    ) -> dict[str, Any]:
        deadline = self._clock() + float(
            timeout if timeout is not None else request.get("timeout", 30)
        )
        last: BaseException | None = None
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            if self._is_cancelled(jid):
                raise JobCancelledError("cancelled during execution", details={"job_id": jid})
            if self._clock() > deadline:
                raise TransientError(
                    "operation timeout", details={"timeout": timeout or request.get("timeout", 30)}
                )
            try:
                self.store.update_job(jid, "running", attempts=attempt)
                return webgpu.run_domain(request, max_workgroups=self.config.max_workgroups)
            except (JobCancelledError, ValidationError, QuotaExceededError):
                raise
            except TransientError as exc:
                last = exc
                self.store.emit("retry", jid, {"attempt": attempt, "error": str(exc)})
                self.metrics.inc("retries")
                if attempt >= self.retry_policy.max_attempts:
                    break
                self._sleep(self.retry_policy.delay_for(attempt + 1))
        assert last is not None
        raise last

    def _attempts(self, jid: str) -> int:
        job = self.store.get_job(jid)
        return int(job["attempts"] or 0) if job else 0

    def _is_cancelled(self, jid: str) -> bool:
        with self._lock:
            if self._cancel.get(jid):
                return True
        job = self.store.get_job(jid)
        return bool(job and job["state"] == "cancelled")

    def cancel(self, jid: str) -> bool:
        with self._lock:
            self._cancel[jid] = True
        return self.store.cancel(jid)

    def recover(self) -> list[dict[str, Any]]:
        """Re-run jobs left non-terminal by a crash. Deterministic order."""
        recovered: list[dict[str, Any]] = []
        for job in reversed(self.store.list_jobs(1000)):
            if job["state"] not in {"queued", "running"}:
                continue
            jid = job["id"]
            request = json.loads(job["request"])
            with self._lock:
                self._cancel[jid] = False
            try:
                self.store.update_job(jid, "recovering", attempts=int(job["attempts"] or 0) + 1)
                result = webgpu.run_domain(request, max_workgroups=self.config.max_workgroups)
                self.store.update_job(
                    jid, "succeeded", result, attempts=int(job["attempts"] or 0) + 1
                )
                recovered.append({"job_id": jid, "state": "succeeded"})
                self.metrics.inc("jobs_recovered")
            except Exception as exc:  # noqa: BLE001 - recorded per job
                self.store.update_job(
                    jid, "failed", error=f"recovery failed: {type(exc).__name__}: {exc}"
                )
                recovered.append({"job_id": jid, "state": "failed"})
            finally:
                with self._lock:
                    self._cancel.pop(jid, None)
        return recovered

    def _validate_request(self, request: Mapping[str, Any]) -> None:
        if not isinstance(request, Mapping):
            raise ValidationError(
                "request must be an object", details={"type": type(request).__name__}
            )
        size = len(canonical(dict(request)))
        if size > self.config.max_payload_bytes:
            raise QuotaExceededError(
                "request exceeds payload quota",
                details={"bytes": size, "limit": self.config.max_payload_bytes},
            )
        version = str(request.get("schema_version", SCHEMA_VERSION))
        if version != SCHEMA_VERSION:
            raise ValidationError(
                "unsupported request schema_version",
                details={"schema_version": version, "supported": SCHEMA_VERSION},
            )

    # -- simulation and benchmark -----------------------------------------
    def simulate(self) -> dict[str, Any]:
        """Replay the failure modes the roadmap's Phase 1.2 requires."""
        outcomes: dict[str, Any] = {}
        outcomes["success"] = self.run({"operations": 1e6, "cache": False}).state
        try:
            self.run("not-an-object")  # type: ignore[arg-type]
        except WebGPUError as exc:
            outcomes["malformed_input"] = type(exc).__name__
        try:
            self.run({"operations": 1e6, "prefer": "quantum"})
        except WebGPUError as exc:
            outcomes["invalid_backend"] = type(exc).__name__
        try:
            self.run({"operations": 1e6, "memory_mb": -1})
        except WebGPUError as exc:
            outcomes["invalid_memory"] = type(exc).__name__
        try:
            self.run({"operations": 1e9, "cache": False})
        except WebGPUError as exc:
            outcomes["overload"] = type(exc).__name__
        outcomes["restart_recovery"] = self.recover()
        return outcomes

    def benchmark(self, runs: int = 5) -> dict[str, Any]:
        """Measure real latency and throughput for the core operation."""
        if runs < 1:
            raise ValidationError("runs must be >= 1", details={"runs": runs})
        latencies: list[float] = []
        sizes: list[int] = []
        for _ in range(int(runs)):
            request = {"operations": 1e6, "cache": False}
            started = self._clock()
            out = self.run(request)
            latencies.append((self._clock() - started) * 1000.0)
            sizes.append(len(canonical(out.to_dict())))
        ordered = sorted(latencies)
        avg = sum(latencies) / len(latencies)
        return {
            "runs": int(runs),
            "latency_ms_avg": round(avg, 4),
            "latency_ms_p95": round(ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)], 4),
            "throughput_per_sec": round(1000.0 / max(0.001, avg), 3),
            "result_bytes_avg": round(sum(sizes) / len(sizes), 1),
            "memory_rss_kb": _rss_kb(),
        }


def _rss_kb() -> int | None:
    try:
        import resource

        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except Exception:  # noqa: BLE001 - platform dependent
        return None
