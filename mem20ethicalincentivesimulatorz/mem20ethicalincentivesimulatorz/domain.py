"""Ethical incentive simulator: rewards, fairness, alignment."""
import math


def incentive(value, effort, fairness_weight=0.5):
    base = value * effort
    fairness_penalty = abs(value - effort) * fairness_weight
    return round(base - fairness_penalty, 4)


def fairness_score(distribution):
    if not distribution:
        return 0.0
    mean = sum(distribution) / len(distribution)
    variance = sum((x - mean) ** 2 for x in distribution) / len(distribution)
    # coefficient of variation inverted
    if mean == 0:
        return 0.0
    cv = (variance ** 0.5) / mean
    return round(max(0.0, 1 - cv), 4)


def align_reward(action, ethical_score):
    base = action.get("reward", 0)
    if ethical_score < 0.3:
        return 0.0
    return round(base * ethical_score, 4)


def simulate_incentives(agents, rounds=10):
    out = []
    for r in range(rounds):
        total = sum(a.get("effort", 0) for a in agents)
        for a in agents:
            reward = incentive(a.get("value", 1), a.get("effort", 1))
            a["cumulative"] = a.get("cumulative", 0) + reward
        out.append({"round": r + 1, "total_reward": round(sum(a.get("cumulative", 0) for a in agents), 2)})
    return out


def ethical_violation(action):
    return action.get("harm", 0) > 0 or action.get("deceptive", False)
