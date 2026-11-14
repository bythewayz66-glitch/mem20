"""Circuit breaker that stops hammering a failing dependency.

Domain research: closed -> open -> half-open. Closed passes traffic and counts
failures; past the threshold it opens and fails fast without touching the
dependency; after a cool-down it admits one probe, and that probe decides
whether to close again. The property that matters is fail-fast: once open, a
call must not reach the dependency at all, which is directly observable.
"""

from __future__ import annotations

import threading
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


class CircuitOpen(RuntimeError):
    pass


class FaultContainmentCells:
    def __init__(self, threshold=5, cool_down=30.0):
        if threshold < 1:
            raise ValueError("threshold must be >= 1")
        self.threshold = int(threshold)
        self.cool_down = float(cool_down)
        self._failures = 0
        self._opened_at = None
        self._state = "closed"
        self._lock = threading.Lock()

    @property
    def state(self):
        with self._lock:
            if self._state == "open":
                return self._state
            return self._state

    def _maybe_half_open(self, now):
        if self._state == "open" and (now - self._opened_at) >= self.cool_down:
            self._state = "half-open"
        return self._state

    def call(self, fn, now=0.0):
        with self._lock:
            st = self._maybe_half_open(now)
            if st == "open":
                raise CircuitOpen("circuit open; dependency not called")
            probing = (st == "half-open")
        try:
            result = fn()
        except Exception:
            with self._lock:
                self._failures += 1
                if probing or self._failures >= self.threshold:
                    self._state = "open"
                    self._opened_at = now
            raise
        else:
            with self._lock:
                if probing or self._failures == 0:
                    self._state = "closed"
                    self._failures = 0
            return result


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("fcc-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "fcc-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.index_health()
        ctx["engine_status_checked"] = True
    return ctx
