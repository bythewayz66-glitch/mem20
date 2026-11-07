"""Dynamic quest reward composer: quest gen, reward scaling, balancing, with estate report."""
from __future__ import annotations
import random, math
from . import ecosystem
__all__=["generate_quest","reward_for_quest","balance_quests","quest_chain","completion_rate","quest_report","probe","estate_context"]

def generate_quest(difficulty=1, seed=0):
    rng = random.Random(seed)
    objectives = ["collect", "defeat", "explore", "deliver"]
    targets = ["goblins", "artifacts", "ruins", "packages"]
    return {"id": f"q-{seed}", "objective": rng.choice(objectives), "target": rng.choice(targets), "count": rng.randint(1, 5) * difficulty, "difficulty": difficulty}

def reward_for_quest(quest, player_level=1):
    base = quest["count"] * 10 * quest["difficulty"]
    level_bonus = player_level * 5
    return {"xp": base + level_bonus, "gold": base // 2, "items": ["potion"] if quest["difficulty"] >= 2 else []}

def balance_quests(quests):
    total_reward = sum(q.get("reward", 0) for q in quests)
    avg = total_reward / max(1, len(quests))
    for q in quests:
        q["balanced"] = abs(q.get("reward", 0) - avg) < avg * 0.5
    return quests

def quest_chain(quests):
    return sorted(quests, key=lambda q: q.get("difficulty", 1))

def completion_rate(completions, total):
    if total == 0: return 0.0
    return round(completions / total, 4)

def quest_report():
    q=generate_quest(2, seed=1); rew=reward_for_quest(q, player_level=3); qs=[{"reward":50},{"reward":60},{"reward":55}]; balanced=balance_quests([dict(x) for x in qs]); rate=completion_rate(7,10)
    peers={
        "challenge_context": ecosystem.challenge_context(),
        "narrative_hooks": ecosystem.narrative_hooks(),
        "quest_events": ecosystem.quest_events("quest.report", {"quest":q.get("id"),"xp":rew.get("xp")}),
        "loyalty_rewards": ecosystem.loyalty_rewards(["quest","reward"]),
        "capability_routing": ecosystem.capability_routing("quest", ["compose","balance","reward"]),
        "lifecycle_retention": ecosystem.lifecycle_retention(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"quest_id":q.get("id"),"xp":rew.get("xp"),"balanced_count":sum(1 for x in balanced if x.get("balanced")),"completion_rate":rate,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=quest_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
