"""Token-bucket and leaky-bucket rate limiting.

Domain research: these two answer different questions and get confused. A
token bucket lets a burst through up to its capacity, then enforces a steady
rate - correct for protecting a backend that can absorb short spikes. A leaky
bucket smooths output to a constant rate with no burst allowance - correct when
the downstream cannot spike at all. Both must REFUSE rather than silently
wait forever, so the caller learns it was throttled.
"""
import threading, time


class Throttled(RuntimeError):
    pass


class TokenBucket:
    def __init__(self, rate_per_sec, capacity=None):
        if rate_per_sec <= 0:
            raise ValueError("rate must be positive")
        self.rate = float(rate_per_sec)
        self.capacity = float(capacity if capacity is not None else rate_per_sec)
        self._tokens = self.capacity
        # None, not time.monotonic(): seeding from the real clock while
        # allow() accepts an injected `now` made the first injected call
        # compute a huge negative elapsed and drain a full bucket. The first
        # observation now simply establishes the baseline.
        self._last = None
        self._lock = threading.Lock()

    def _refill(self, now=None):
        now = time.monotonic() if now is None else now
        if self._last is not None:
            self._tokens = min(self.capacity,
                               self._tokens + (now - self._last) * self.rate)
        self._last = now

    def allow(self, cost=1.0, now=None):
        with self._lock:
            self._refill(now)
            if self._tokens >= cost:
                self._tokens -= cost
                return True
            return False

    def retry_after(self, cost=1.0, now=None):
        with self._lock:
            self._refill(now)
            return max(0.0, (cost - self._tokens) / self.rate)

    @property
    def tokens(self):
        return self._tokens


class LeakyBucket:
    """Constant output rate, no burst allowance."""

    def __init__(self, rate_per_sec):
        if rate_per_sec <= 0:
            raise ValueError("rate must be positive")
        self.rate = float(rate_per_sec)
        self._level = 0.0
        self._last = None      # same baseline fix as TokenBucket
        self._lock = threading.Lock()

    def _leak(self, now=None):
        now = time.monotonic() if now is None else now
        if self._last is not None:
            self._level = max(0.0, self._level - (now - self._last) * self.rate)
        self._last = now

    def allow(self, cost=1.0, now=None):
        with self._lock:
            self._leak(now)
            self._level += cost
            return self._level <= self.rate

    def drain_time(self, now=None):
        with self._lock:
            self._leak(now)
            return self._level / self.rate

    @property
    def level(self):
        return self._level
