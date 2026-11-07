"""Player motivation twin: model player motivation over time, with estate report."""
from __future__ import annotations
import time
from . import ecosystem
__all__=["create_twin","update","predict_churn","motivation_segments","twin_health","motivation_report","probe","estate_context"]

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
    if twin["motivation"] >= 0.7: return "high"
    if twin["motivation"] >= 0.4: return "medium"
    return "low"

def twin_health(twin):
    return {"motivation": twin["motivation"], "events": len(twin["history"]), "churn_risk": predict_churn(twin)}

def motivation_report(player="p1"):
    twin=create_twin(player); update(twin,{"delta":0.2,"reason":"quest"}); update(twin,{"delta":-0.1,"reason":"loss"})
    health=twin_health(twin); seg=motivation_segments(twin)
    peers={
        "lifecycle_context": ecosystem.lifecycle_context(),
        "quest_motivation": ecosystem.quest_motivation(),
        "challenge_engagement": ecosystem.challenge_engagement(),
        "motivation_scenarios": ecosystem.motivation_scenarios(twin["motivation"]),
        "motivation_events": ecosystem.motivation_events("motivation.report", {"player":player,"motivation":twin["motivation"],"segment":seg}),
        "capability_routing": ecosystem.capability_routing(player, ["motivate","retain","reward"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"motivation":twin["motivation"],"segment":seg,"health":health,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=motivation_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
