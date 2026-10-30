"""Self-tuning resource governor: adjust quotas dynamically."""
import time


def govern(resources, usage, thresholds):
    actions = []
    for r, u in usage.items():
        cap = resources.get(r, 0)
        if cap > 0 and u / cap > thresholds.get(r, 0.8):
            actions.append({"resource": r, "action": "throttle", "usage": u, "cap": cap})
        elif cap > 0 and u / cap < thresholds.get(r, 0.8) * 0.3:
            actions.append({"resource": r, "action": "release", "usage": u, "cap": cap})
    return actions


def adjust_quota(resource, current, target_usage):
    if target_usage > 0.8:
        return current * 1.2
    if target_usage < 0.3:
        return current * 0.8
    return current


def governor_health(resources, usage):
    return {"resources": len(resources), "overloaded": sum(1 for r,u in usage.items() if resources.get(r,0)>0 and u/resources[r]>0.8)}
