"""Player motivation twin: model player motivation over time."""
import time


def create_twin(player):
    return {"player": player, "motivation": 0.5, "history": [], "last_update": time.time()}


def update(twin, event):
    delta = event.get("delta", 0)
    twin["motivation"] = max(0, min(1, twin["motivation"] + delta))
    twin["history"].append({"event": event, "motivation": twin["motivation"], "ts": time.time()})
    twin["last_update"] = time.time()
    return twin


def predict_churn(twin, threshold=0.2):
    return twin["motivation"] < threshold


def motivation_segments(twin):
    if twin["motivation"] >= 0.7:
        return "high"
    if twin["motivation"] >= 0.4:
        return "medium"
    return "low"


def twin_health(twin):
    return {"motivation": twin["motivation"], "events": len(twin["history"]), "churn_risk": predict_churn(twin)}
