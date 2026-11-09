"""AI pipeline cost optimizer: stage costs, bottleneck detection, optimization."""

from __future__ import annotations

import math
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def stage_cost(stage, throughput):
    """Cost for a stage given throughput (units/sec)."""
    base = float(stage.get("base_cost", 1.0))
    per_unit = float(stage.get("cost_per_unit", 0.01))
    return round(base + per_unit * throughput, 4)


def pipeline_cost(stages, throughput):
    """Total pipeline cost for given throughput."""
    return round(sum(stage_cost(s, throughput) for s in stages), 4)


def bottleneck(stages, throughputs):
    """Find the bottleneck stage (min throughput)."""
    if not stages:
        return None
    tps = [(s.get("id", i), throughputs.get(s.get("id", i), 0)) for i, s in enumerate(stages)]
    return min(tps, key=lambda x: x[1])


def optimize_throughput(stages, budget):
    """Given budget, find max uniform throughput."""
    if not stages:
        return 0.0
    lo, hi = 0.0, 1000.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if pipeline_cost(stages, mid) <= budget:
            lo = mid
        else:
            hi = mid
    return round(lo, 4)


def cost_breakdown(stages, throughput):
    """Per-stage cost breakdown."""
    return [{"id": s.get("id", i), "cost": stage_cost(s, throughput)} for i, s in enumerate(stages)]


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("aipco-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "aipco-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
