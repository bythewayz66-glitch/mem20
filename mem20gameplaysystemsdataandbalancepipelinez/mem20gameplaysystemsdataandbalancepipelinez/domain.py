"""Gameplay systems data & balance pipeline: telemetry, analysis, tuning."""
import math


def collect_telemetry(events):
    return {"events": len(events), "unique_players": len({e.get("player") for e in events}), "actions": {}}


def aggregate_metrics(telemetry):
    actions = {}
    for e in telemetry.get("raw", []):
        a = e.get("action")
        actions[a] = actions.get(a, 0) + 1
    return {"action_counts": actions, "total": len(telemetry.get("raw", []))}


def balance_tuning(metrics, targets):
    adjustments = []
    for k, target in targets.items():
        actual = metrics.get(k, 0)
        if actual != target:
            adjustments.append({"param": k, "current": actual, "target": target, "delta": target - actual})
    return adjustments


def funnel_analysis(steps):
    rates = []
    for i in range(1, len(steps)):
        prev = steps[i - 1].get("count", 0)
        cur = steps[i].get("count", 0)
        rate = cur / max(1, prev)
        rates.append({"step": steps[i].get("name"), "conversion": round(rate, 4)})
    return rates


def pipeline_report(data):
    return {"records": len(data), "valid": sum(1 for d in data if d.get("valid")), "invalid": sum(1 for d in data if not d.get("valid"))}
