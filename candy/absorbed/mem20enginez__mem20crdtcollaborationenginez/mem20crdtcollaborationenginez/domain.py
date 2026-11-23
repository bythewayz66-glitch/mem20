"""G-Counter and PN-Counter merge without a coordinator.

Domain research: counters that only ever grow commute and are idempotent, so
concurrent increments from any number of nodes merge by taking the maximum per
replica. That is what makes them safe without locking. The property worth
testing is not that they add up, but that merge is order-independent and
double-count-free - apply the same update twice and the result must not change.
"""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class GCounter:
    """Grow-only counter. Merges by per-replica max."""
    counts: Dict[str, int] = field(default_factory=dict)

    def increment(self, replica, n=1):
        if n < 0:
            raise ValueError("G-Counter cannot decrement; use PN-Counter")
        self.counts[replica] = self.counts.get(replica, 0) + int(n)
        return self.value

    @property
    def value(self):
        return sum(self.counts.values())

    def merge(self, other):
        for r, v in other.counts.items():
            self.counts[r] = max(self.counts.get(r, 0), v)
        return self


@dataclass
class PNCounter:
    """Positive/negative counter: one G-Counter each way."""
    pos: GCounter = field(default_factory=GCounter)
    neg: GCounter = field(default_factory=GCounter)

    def increment(self, replica, n=1):
        self.pos.increment(replica, n); return self.value

    def decrement(self, replica, n=1):
        self.neg.increment(replica, n); return self.value

    @property
    def value(self):
        return self.pos.value - self.neg.value

    def merge(self, other):
        self.pos.merge(other.pos); self.neg.merge(other.neg); return self
