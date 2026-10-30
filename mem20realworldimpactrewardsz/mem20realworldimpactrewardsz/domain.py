"""Real-world impact rewards: track impact, compute rewards."""
import time


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
