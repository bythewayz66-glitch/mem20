"""Capability routing by consistent hashing.

Domain research: consistent hashing with virtual nodes, so rebalancing when a
capability is added or removed touches O(1/n) of the keyspace instead of
reshuffling everything. That property is the entire reason it exists, and it
is directly testable: removing a node must move strictly fewer than half the
keys relative to its share.
"""

from __future__ import annotations

import bisect
import hashlib
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


class CapabilityMarketplace:
    def __init__(self, replicas=160):
        if replicas < 1:
            raise ValueError("replicas must be >= 1")
        self.replicas = int(replicas)
        self._ring = []
        self._owners = {}

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


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("cm-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "cm-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
