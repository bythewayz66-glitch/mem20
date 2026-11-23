"""Self-tuning resource governor: adjust quotas dynamically, with estate report."""
from __future__ import annotations
from . import ecosystem
__all__=["govern","adjust_quota","governor_health","governor_report","probe","estate_context"]

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

def governor_report():
    resources={"cpu":100,"mem":100}; usage={"cpu":90,"mem":10}; thresholds={"cpu":0.8,"mem":0.8}
    actions=govern(resources,usage,thresholds); h=governor_health(resources,usage); adj=adjust_quota("cpu",100,0.9)
    peers={
        "demand_forecast": ecosystem.demand_forecast([80,85,90]),
        "causal_tuning": ecosystem.causal_tuning({"overloaded":h["overloaded"]},{"overloaded":1}),
        "tuning_containment": ecosystem.tuning_containment("throttle"),
        "governor_events": ecosystem.governor_events("governor.actions", {"actions":len(actions),"overloaded":h["overloaded"]}),
        "capacity_routing": ecosystem.capacity_routing("cpu", ["govern","throttle","scale"]),
        "recovery_director": ecosystem.recovery_director(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and len(actions)>=1,"actions":actions,"health":h,"adjusted":adj,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=governor_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
