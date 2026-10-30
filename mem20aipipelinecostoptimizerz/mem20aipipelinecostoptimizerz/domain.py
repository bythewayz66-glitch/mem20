"""AI pipeline cost optimizer: stage costs, bottleneck detection, optimization."""
import math


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
    # binary search
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
