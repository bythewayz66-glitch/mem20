"""Reward forge: craft reward functions for RL, with estate report."""
from __future__ import annotations
import math
from . import ecosystem
__all__=["linear_reward","shaped_reward","normalize","reward_health","forge_report","probe","estate_context"]

def linear_reward(state, weights):
    return sum(weights.get(k, 0) * state.get(k, 0) for k in weights)

def shaped_reward(base, shaping):
    return base + shaping

def normalize(rewards):
    if not rewards: return []
    mn, mx = min(rewards), max(rewards); rng = mx - mn or 1
    return [(r - mn) / rng for r in rewards]

def reward_health(rewards):
    if not rewards: return {"count": 0}
    return {"count": len(rewards), "mean": sum(rewards)/len(rewards), "min": min(rewards), "max": max(rewards)}

def forge_report():
    base=linear_reward({"a":2,"b":1},{"a":1.0,"b":0.5}); shaped=shaped_reward(base,0.5); vals=normalize([1,2,3,4]); h=reward_health([1,2,3])
    peers={
        "quest_reward_shapes": ecosystem.quest_reward_shapes(),
        "impact_rewards": ecosystem.impact_rewards(),
        "counterfactual_shaping": ecosystem.counterfactual_shaping({"reward":base}),
        "reward_events": ecosystem.reward_events("reward.forged", {"base":base,"shaped":shaped}),
        "reward_routing": ecosystem.reward_routing("forge", ["linear","shape","normalize"]),
        "causal_weighting": ecosystem.causal_weighting({"a":2},{"a":1}),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"base":base,"shaped":shaped,"normalized_len":len(vals),"health":h,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=forge_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
