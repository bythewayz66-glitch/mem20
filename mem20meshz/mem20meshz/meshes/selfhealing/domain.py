"""Retry with exponential backoff and jitter, then give up loudly.

Domain research: naive fixed-interval retry synchronises every client onto the
same moment and produces a thundering herd exactly when the dependency is
recovering. Exponential backoff with jitter spreads them. The property that
matters is that delay grows and that a permanently failing dependency raises
after the budget rather than retrying forever.
"""
import random, time


class RetriesExhausted(RuntimeError):
    pass


class SelfHealingConnectorMesh:
    def __init__(self, base_delay=0.1, factor=2.0, max_delay=30.0,
                 jitter=True, rng=None):
        if base_delay < 0:
            raise ValueError("base_delay must be >= 0")
        if factor < 1:
            raise ValueError("factor must be >= 1")
        self.base_delay = float(base_delay)
        self.factor = float(factor)
        self.max_delay = float(max_delay)
        self.jitter = bool(jitter)
        self.rng = rng or random.Random(0)
        self.attempts = 0

    def delay_for(self, attempt):
        """Delay before attempt N (0-indexed), capped and jittered."""
        raw = self.base_delay * (self.factor ** max(0, attempt - 1))
        capped = min(raw, self.max_delay)
        if not self.jitter:
            return capped
        return self.rng.uniform(capped / 2.0, capped)

    def call(self, fn, retries=3, sleep=time.sleep):
        last = None
        for attempt in range(retries + 1):
            self.attempts += 1
            try:
                return fn()
            except Exception as exc:
                last = exc
                if attempt == retries:
                    break
                sleep(self.delay_for(attempt + 1))
        raise RetriesExhausted(
            f"failed after {retries + 1} attempts: {type(last).__name__}: {last}") from last

    def call_if_transient(self, fn, is_transient, retries=3, sleep=time.sleep):
        """Only retry failures classified as transient. A 400 is not retried."""
        for attempt in range(retries + 1):
            self.attempts += 1
            try:
                return fn()
            except Exception as exc:
                if not is_transient(exc):
                    raise
                last = exc
                if attempt == retries:
                    break
                sleep(self.delay_for(attempt + 1))
        raise RetriesExhausted(
            f"failed after {retries + 1} attempts: {type(last).__name__}: {last}") from last
