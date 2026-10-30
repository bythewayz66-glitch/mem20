"""Execution digital twin: process mirror, simulation, prediction."""
import math, random


def create_twin(process):
    return {"id": process.get("id"), "state": process.get("state", {}), "metrics": process.get("metrics", {}), "synced_at": 0}


def sync_twin(twin, real_state):
    twin["state"] = dict(real_state)
    import time
    twin["synced_at"] = time.time()
    return twin


def simulate(twin, actions):
    results = []
    state = dict(twin.get("state", {}))
    for a in actions:
        state.update(a.get("effect", {}))
        results.append({"action": a.get("name"), "state": dict(state)})
    return results


def predict_outcome(twin, action):
    base = twin.get("metrics", {}).get("success_rate", 0.5)
    effect = action.get("impact", 0.0)
    return round(min(1.0, max(0.0, base + effect)), 4)


def drift(twin, real_state):
    diffs = {}
    for k in set(twin.get("state", {})) | set(real_state):
        if twin.get("state", {}).get(k) != real_state.get(k):
            diffs[k] = {"twin": twin.get("state", {}).get(k), "real": real_state.get(k)}
    return diffs
