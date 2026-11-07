"""Community challenge engine: challenges, participation, leaderboards, rewards, with estate report."""
from __future__ import annotations
import time
from . import ecosystem
__all__=["create_challenge","join","record_progress","leaderboard","check_completion","reward_pool","challenge_report","probe","estate_context"]

def create_challenge(name, goal, duration_days=7):
    return {"name": name, "goal": goal, "duration_days": duration_days, "participants": {}, "start": time.time(), "status": "active"}

def join(challenge, user):
    if user not in challenge["participants"]: challenge["participants"][user] = 0
    return challenge

def record_progress(challenge, user, amount):
    if user in challenge["participants"]: challenge["participants"][user] += amount
    return challenge

def leaderboard(challenge):
    items = sorted(challenge["participants"].items(), key=lambda x: -x[1])
    return [{"user": u, "score": s, "rank": i + 1} for i, (u, s) in enumerate(items)]

def check_completion(challenge):
    for user, score in challenge["participants"].items():
        if score >= challenge["goal"]: return {"completed": True, "winner": user}
    return {"completed": False, "winner": None}

def reward_pool(challenge, total_reward):
    lb = leaderboard(challenge)
    if not lb: return {}
    splits = [0.5, 0.3, 0.2]; out = {}
    for i, entry in enumerate(lb[:3]): out[entry["user"]] = round(total_reward * splits[i], 2)
    return out

def challenge_report(name="weekly", goal=10, users=None, total_reward=100.0):
    users = users or ["a","b","c"]
    ch = create_challenge(name, goal)
    for u in users: join(ch,u)
    for i,u in enumerate(users): record_progress(ch,u,(i+1)*4)
    lb=leaderboard(ch); done=check_completion(ch); rewards=reward_pool(ch,total_reward)
    peers={
        "quest_rewards": ecosystem.quest_rewards(goal, level=1),
        "challenge_events": ecosystem.challenge_events("challenge.report", {"name":name,"participants":len(users),"completed":done["completed"]}),
        "loyalty_signal": ecosystem.loyalty_signal(["community","challenges"]),
        "engagement_signal": ecosystem.engagement_signal(len(users)),
        "reward_routing": ecosystem.reward_routing(name, ["rewards","badges"]),
        "lifecycle_signal": ecosystem.lifecycle_signal(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"leaderboard":lb,"completion":done,"rewards":rewards,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=challenge_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
