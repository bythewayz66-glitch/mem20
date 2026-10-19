"""Circuit breaker that stops hammering a failing dependency.

Domain research: closed -> open -> half-open. Closed passes traffic and counts
failures; past the threshold it opens and fails fast without touching the
dependency; after a cool-down it admits one probe, and that probe decides
whether to close again. The property that matters is fail-fast: once open, a
call must not reach the dependency at all, which is directly observable.
"""
import threading


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
