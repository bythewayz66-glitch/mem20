"""Executable design stress lab: load, stress, resilience testing."""
import random, math


def stress_test(system, load_multiplier=2.0, duration_s=60):
    base = system.get("base_load", 100)
    peak = base * load_multiplier
    results = []
    for t in range(0, duration_s, 5):
        load = base + (peak - base) * (t / duration_s)
        capacity = system.get("capacity", 200)
        util = load / capacity
        results.append({"t": t, "load": round(load, 1), "utilization": round(util, 3), "ok": util < 0.95})
    return results


def resilience_score(results):
    ok_count = sum(1 for r in results if r.get("ok"))
    return round(ok_count / max(1, len(results)), 4)


def bottleneck_analysis(system):
    components = system.get("components", [])
    if not components:
        return []
    return sorted(components, key=lambda c: -c.get("load", 0))[:3]


def recovery_time(system, failure_type="crash"):
    base = {"crash": 30, "degradation": 10, "partition": 60}.get(failure_type, 30)
    redundancy = system.get("redundancy", 1)
    return round(base / max(1, redundancy), 2)


def design_verdict(results, threshold=0.9):
    score = resilience_score(results)
    return {"pass": score >= threshold, "score": score, "threshold": threshold}
