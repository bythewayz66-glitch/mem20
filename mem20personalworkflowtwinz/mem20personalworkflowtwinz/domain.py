"""Personal workflow twin: mirror user workflows, suggest improvements."""
import time


def create_twin(user, workflows=None):
    return {"user": user, "workflows": list(workflows or []), "patterns": [], "created": time.time()}


def observe(twin, event):
    twin["patterns"].append(event)
    return twin


def suggest_improvements(twin):
    suggestions = []
    # detect repeated manual steps
    from collections import Counter
    steps = [e.get("action") for e in twin["patterns"] if e.get("action")]
    for action, cnt in Counter(steps).items():
        if cnt >= 3:
            suggestions.append({"action": action, "count": cnt, "suggestion": "automate"})
    return suggestions


def efficiency_score(twin):
    if not twin["patterns"]:
        return 1.0
    manual = sum(1 for e in twin["patterns"] if e.get("manual"))
    return round(1 - manual / len(twin["patterns"]), 4)


def twin_health(twin):
    return {"workflows": len(twin["workflows"]), "patterns": len(twin["patterns"]), "efficiency": efficiency_score(twin)}
