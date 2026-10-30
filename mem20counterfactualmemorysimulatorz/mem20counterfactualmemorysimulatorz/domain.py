"""Counterfactual memory simulator: what-if, branching, replay."""
import copy


def branch(memory, change):
    m = copy.deepcopy(memory)
    m["state"] = {**m.get("state", {}), **change}
    m["branch"] = m.get("branch", 0) + 1
    return m


def replay(memory, steps):
    states = [copy.deepcopy(memory)]
    cur = copy.deepcopy(memory)
    for s in steps:
        cur["state"] = {**cur.get("state", {}), **s}
        states.append(copy.deepcopy(cur))
    return states


def counterfactual(original, intervention):
    cf = copy.deepcopy(original)
    cf["intervention"] = intervention
    cf["state"] = {**cf.get("state", {}), **intervention.get("change", {})}
    return cf


def compare(original, counterfactual):
    diffs = {}
    for k in set(original.get("state", {})) | set(counterfactual.get("state", {})):
        if original.get("state", {}).get(k) != counterfactual.get("state", {}).get(k):
            diffs[k] = {"original": original.get("state", {}).get(k), "counterfactual": counterfactual.get("state", {}).get(k)}
    return diffs


def outcome_probability(memory, action):
    base = memory.get("base_rate", 0.5)
    boost = action.get("effect", 0.0)
    return min(1.0, max(0.0, base + boost))
