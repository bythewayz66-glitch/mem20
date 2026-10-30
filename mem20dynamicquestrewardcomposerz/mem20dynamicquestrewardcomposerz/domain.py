"""Dynamic quest reward composer: quest gen, reward scaling, balancing."""
import random, math


def generate_quest(difficulty=1, seed=0):
    rng = random.Random(seed)
    objectives = ["collect", "defeat", "explore", "deliver"]
    targets = ["goblins", "artifacts", "ruins", "packages"]
    return {
        "id": f"q-{seed}",
        "objective": rng.choice(objectives),
        "target": rng.choice(targets),
        "count": rng.randint(1, 5) * difficulty,
        "difficulty": difficulty,
    }


def reward_for_quest(quest, player_level=1):
    base = quest["count"] * 10 * quest["difficulty"]
    level_bonus = player_level * 5
    return {"xp": base + level_bonus, "gold": base // 2, "items": ["potion"] if quest["difficulty"] >= 2 else []}


def balance_quests(quests):
    # normalize rewards so total is fair
    total_reward = sum(q.get("reward", 0) for q in quests)
    avg = total_reward / max(1, len(quests))
    for q in quests:
        q["balanced"] = abs(q.get("reward", 0) - avg) < avg * 0.5
    return quests


def quest_chain(quests):
    return sorted(quests, key=lambda q: q.get("difficulty", 1))


def completion_rate(completions, total):
    if total == 0:
        return 0.0
    return round(completions / total, 4)
