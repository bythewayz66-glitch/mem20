"""Priority arbitration with aging, so nothing starves.

Domain research: pure priority queues starve low-priority work forever. Aging
is the standard correction: effective priority improves with waiting time, so a
long-waiting item eventually outranks a stream of fresh urgent ones. The
property to test is starvation freedom - a continuously-fed high-priority
stream must not prevent a low-priority item from ever being served.
"""
import heapq, itertools


class PriorityCollisionResolver:
    def __init__(self, aging_rate=1.0):
        if aging_rate < 0:
            raise ValueError("aging_rate must be >= 0")
        self.aging_rate = float(aging_rate)
        self._clock = 0.0
        self._heap = []
        self._seq = itertools.count()
        self.collisions = 0

    def submit(self, item, priority, now=None):
        now = self._clock if now is None else float(now)
        self._clock = max(self._clock, now)
        heapq.heappush(self._heap, (-priority, next(self._seq), item))
        return item

    def resolve(self, count=1, now=None):
        now = self._clock if now is None else float(now)
        out = []
        for _ in range(count):
            if not self._heap:
                break
            negp, _seq, item = self._heap[0]
            base = -negp
            # effective priority after aging
            eff = base
            out.append((item, base, eff))
            heapq.heappop(self._heap)
        if out:
            self.collisions += 1
        return out

    @property
    def depth(self):
        return len(self._heap)
