"""Capability routing by consistent hashing.

Domain research: consistent hashing with virtual nodes, so rebalancing when a
capability is added or removed touches O(1/n) of the keyspace instead of
reshuffling everything. That property is the entire reason it exists, and it
is directly testable: removing a node must move strictly fewer than half the
keys relative to its share.
"""
import bisect, hashlib


class CapabilityMarketplace:
    def __init__(self, replicas=160):
        if replicas < 1:
            raise ValueError("replicas must be >= 1")
        self.replicas = int(replicas)
        self._ring = []        # sorted hashes
        self._owners = {}      # hash -> capability

    @staticmethod
    def _h(key):
        return int(hashlib.sha256(str(key).encode()).hexdigest()[:16], 16)

    def add(self, capability):
        for r in range(self.replicas):
            h = self._h(f"{capability}#{r}")
            self._owners[h] = capability
        self._ring = sorted(self._owners)
        return len(self._ring)

    def remove(self, capability):
        for r in range(self.replicas):
            self._owners.pop(self._h(f"{capability}#{r}"), None)
        self._ring = sorted(self._owners)
        return True

    def locate(self, key):
        """Owner for a key: first ring position clockwise from it."""
        if not self._ring:
            return None
        i = bisect.bisect(self._ring, self._h(key))
        return self._owners[self._ring[i % len(self._ring)]]

    def distribution(self, keys=2000):
        from collections import Counter
        return Counter(self.locate(k) for k in range(keys))
