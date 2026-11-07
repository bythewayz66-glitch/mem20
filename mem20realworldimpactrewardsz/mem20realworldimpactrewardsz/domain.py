"""Real-world impact rewards: track impact, compute rewards, with estate report."""
from __future__ import annotations
import time
from . import ecosystem
__all__=["record_impact","compute_reward","leaderboard","impact_health","impact_report","probe","estate_context"]

def record_impact(impacts, user, impact_type, magnitude):
    impacts.setdefault(user, []).append({"type": impact_type, "magnitude": magnitude, "ts": time.time()})
    return impacts

def compute_reward(impacts, user, rate=1.0):
    total = sum(i["magnitude"] for i in impacts.get(user, []))
    return round(total * rate, 4)

def leaderboard(impacts, rate=1.0):
    rows = [{"user": u, "reward": compute_reward(impacts, u, rate)} for u in impacts]
    rows.sort(key=lambda r: -r["reward"])
    return rows

def impact_health(impacts):
    return {"users": len(impacts), "events": sum(len(v) for v in impacts.values())}

def impact_report():
    imp={}; record_impact(imp,"alice","cleanup",2.0); record_impact(imp,"bob","cleanup",1.0); record_impact(imp,"alice","teach",1.5)
    lb=leaderboard(imp); h=impact_health(imp); top=compute_reward(imp,"alice")
    peers={
        "quest_rewards": ecosystem.quest_rewards(top),
        "loyalty_impact": ecosystem.loyalty_impact("alice", top),
        "lifecycle_value": ecosystem.lifecycle_value(),
        "impact_events": ecosystem.impact_events("impact.report", {"events":h["events"],"leader":lb[0]["user"] if lb else None}),
        "reward_routing": ecosystem.reward_routing("rewards", ["compute","leaderboard","record"]),
        "impact_forecast": ecosystem.impact_forecast([1.0,2.0,3.5]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"leaderboard":lb,"events":h["events"],"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=impact_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
