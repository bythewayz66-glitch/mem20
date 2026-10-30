"""Community challenge engine: challenges, leaderboards, rewards."""
import time


def create_challenge(name, goal, duration_days=7):
    return {"name": name, "goal": goal, "duration_days": duration_days, "participants": {}, "start": time.time(), "status": "active"}


def join(challenge, user):
    if user not in challenge["participants"]:
        challenge["participants"][user] = 0
    return challenge


def record_progress(challenge, user, amount):
    if user in challenge["participants"]:
        challenge["participants"][user] += amount
    return challenge


def leaderboard(challenge):
    items = sorted(challenge["participants"].items(), key=lambda x: -x[1])
    return [{"user": u, "score": s, "rank": i + 1} for i, (u, s) in enumerate(items)]


def check_completion(challenge):
    for user, score in challenge["participants"].items():
        if score >= challenge["goal"]:
            return {"completed": True, "winner": user}
    return {"completed": False, "winner": None}


def reward_pool(challenge, total_reward):
    lb = leaderboard(challenge)
    if not lb:
        return {}
    # top 3 split
    splits = [0.5, 0.3, 0.2]
    out = {}
    for i, entry in enumerate(lb[:3]):
        out[entry["user"]] = round(total_reward * splits[i], 2)
    return out
