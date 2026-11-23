"""Fault containment -- first-class memory_engine capability.

Circuit breaker + topic quarantine for failing memory paths.
Formerly mem20faultcontainmentcellsz.
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable


class CircuitOpen(RuntimeError):
    pass


class MemoryCircuit:
    """Fail-fast breaker around a dependency (e.g. vector index, remote store)."""

    def __init__(self, threshold: int = 5, cool_down: float = 30.0):
        if threshold < 1:
            raise ValueError("threshold must be >= 1")
        self.threshold = int(threshold)
        self.cool_down = float(cool_down)
        self._failures = 0
        self._opened_at: float | None = None
        self._state = "closed"
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            if self._state == "open" and self._opened_at is not None:
                if time.time() - self._opened_at >= self.cool_down:
                    self._state = "half-open"
            return self._state

    def call(self, fn: Callable, *args, **kwargs):
        st = self.state
        if st == "open":
            raise CircuitOpen("circuit open; fail-fast")
        try:
            result = fn(*args, **kwargs)
        except Exception:
            with self._lock:
                self._failures += 1
                if self._failures >= self.threshold or st == "half-open":
                    self._state = "open"
                    self._opened_at = time.time()
            raise
        with self._lock:
            self._failures = 0
            self._state = "closed"
            self._opened_at = None
        return result

    def status(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "failures": self._failures,
            "threshold": self.threshold,
            "cool_down": self.cool_down,
            "opened_at": self._opened_at,
        }


def quarantine_topic(topic: str, reason: str = "") -> dict[str, Any]:
    """Mark a topic as quarantined via a grounded marker fact."""
    try:
        from memory_engine import remember
        row = remember(
            topic=f"quarantine:{topic}",
            content=f"quarantined: {reason or 'unspecified'}",
            tags=["quarantine", topic],
            epistemic_status="observed",
        )
        return {"ok": True, "topic": topic, "id": row.get("id") if isinstance(row, dict) else None}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "topic": topic}


def is_quarantined(topic: str) -> bool:
    try:
        from memory_engine import recall
        rows = recall(topic=f"quarantine:{topic}", k=1, include_simulated=False) or []
        return bool(rows)
    except Exception:
        return False


def safe_recall(topic: str | None = None, **kwargs) -> list:
    """recall() that refuses quarantined topics."""
    if topic and is_quarantined(topic):
        return []
    from memory_engine import recall
    return list(recall(topic=topic, **kwargs) or [])


def containment_health() -> dict[str, Any]:
    return {"ok": True, "circuit": MemoryCircuit().status()}
