"""Game balance simulator: stats, DPS, TTK, economy."""
import math


def dps(damage, attack_speed):
    return round(damage * attack_speed, 2)


def ttk(health, dps_val):
    if dps_val <= 0:
        return float("inf")
    return round(health / dps_val, 3)


def economy_balance(income, expenses):
    return round(income - expenses, 2)


def difficulty_curve(levels, base=1.0, growth=1.12):
    return [round(base * (growth ** i), 3) for i in range(levels)]


def balance_check(stats, targets):
    issues = []
    for k, target in targets.items():
        actual = stats.get(k, 0)
        if abs(actual - target) > target * 0.2:
            issues.append({"stat": k, "actual": actual, "target": target})
    return {"balanced": not issues, "issues": issues}


def win_rate(simulations):
    if not simulations:
        return 0.0
    wins = sum(1 for s in simulations if s.get("winner") == "player")
    return round(wins / len(simulations), 4)
