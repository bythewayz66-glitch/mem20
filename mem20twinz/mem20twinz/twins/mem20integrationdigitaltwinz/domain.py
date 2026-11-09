"""Integration digital twin: system mirror, simulation, drift detection."""
import time


def create_twin(system):
    return {"id": system.get("id"), "state": system.get("state", {}), "metrics": system.get("metrics", {}), "synced_at": 0}


def sync(twin, real_state):
    twin["state"] = dict(real_state)
    twin["synced_at"] = time.time()
    return twin


def simulate(twin, scenario):
    if isinstance(scenario, list):
        steps = scenario
    else:
        steps = scenario.get("steps", [])
    state = dict(twin.get("state", {}))
    results = []
    for step in steps:
        state.update(step.get("effect", {}))
        results.append({"step": step.get("name"), "state": dict(state)})
    return results


def drift(twin, real_state):
    diffs = {}
    for k in set(twin.get("state", {})) | set(real_state):
        if twin.get("state", {}).get(k) != real_state.get(k):
            diffs[k] = {"twin": twin.get("state", {}).get(k), "real": real_state.get(k)}
    return diffs


def health(twin):
    return {"synced": twin.get("synced_at", 0) > 0, "drift_count": 0}
