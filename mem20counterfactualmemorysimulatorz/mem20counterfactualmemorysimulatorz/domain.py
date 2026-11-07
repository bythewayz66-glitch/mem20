"""Counterfactual memory simulator: what-if, branching, replay, with estate report."""
from __future__ import annotations
import copy
from . import ecosystem
__all__=["branch","replay","counterfactual","compare","outcome_probability","counterfactual_report","probe","estate_context"]

def branch(memory, change):
    m = copy.deepcopy(memory); m["state"] = {**m.get("state", {}), **change}; m["branch"] = m.get("branch", 0) + 1; return m

def replay(memory, steps):
    states = [copy.deepcopy(memory)]; cur = copy.deepcopy(memory)
    for s in steps: cur["state"] = {**cur.get("state", {}), **s}; states.append(copy.deepcopy(cur))
    return states

def counterfactual(original, intervention):
    cf = copy.deepcopy(original); cf["intervention"] = intervention; cf["state"] = {**cf.get("state", {}), **intervention.get("change", {})}; return cf

def compare(original, counterfactual_state):
    diffs = {}
    for k in set(original.get("state", {})) | set(counterfactual_state.get("state", {})):
        if original.get("state", {}).get(k) != counterfactual_state.get("state", {}).get(k):
            diffs[k] = {"original": original.get("state", {}).get(k), "counterfactual": counterfactual_state.get("state", {}).get(k)}
    return diffs

def outcome_probability(memory, action):
    base = memory.get("base_rate", 0.5); boost = action.get("effect", 0.0)
    return min(1.0, max(0.0, base + boost))

def counterfactual_report(memory=None, intervention=None):
    memory = memory or {"state":{"price":10,"units":100},"base_rate":0.5,"branch":0}
    intervention = intervention or {"change":{"price":11},"effect":0.1}
    b=branch(memory, {"units":110}); rep=replay(memory,[{"units":105},{"units":110}]); cf=counterfactual(memory,intervention); diff=compare(memory,cf); prob=outcome_probability(memory,{"effect":intervention.get("effect",0.1)})
    peers={
        "causal_routing": ecosystem.causal_routing({"price":memory["state"].get("price",10)}, {"price":-0.1}),
        "scenario_events": ecosystem.scenario_events("counterfactual.run", {"diffs":len(diff),"prob":prob}),
        "recovery_paths": ecosystem.recovery_paths("state"),
        "healing_alternatives": ecosystem.healing_alternatives(["branch","replay","rollback"]),
        "demand_scenarios": ecosystem.demand_scenarios([100,105,110,108,112]),
        "scenario_routing": ecosystem.scenario_routing("cf-1", ["simulate","compare"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"branches":b.get("branch"),"replay_steps":len(rep),"diff_keys":len(diff),"outcome_probability":prob,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=counterfactual_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
