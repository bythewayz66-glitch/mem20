"""Goal economy scheduler: resource allocation across goals."""
import math


def schedule_goals(goals, budget):
    # greedy by value/cost ratio
    items = sorted(goals, key=lambda g: g.get("value", 0) / max(0.01, g.get("cost", 1)), reverse=True)
    chosen = []
    used = 0
    for g in items:
        if used + g.get("cost", 0) <= budget:
            chosen.append(g.get("id"))
            used += g.get("cost", 0)
    return {"scheduled": chosen, "budget_used": used, "budget": budget}


def goal_value(goal):
    return goal.get("value", 0) / max(0.01, goal.get("cost", 1))


def rebalance(goals, new_budget):
    return schedule_goals(goals, new_budget)


def progress(goals, completed_ids):
    done = sum(1 for g in goals if g.get("id") in completed_ids)
    return round(done / max(1, len(goals)), 4)


def priority_queue(goals):
    return sorted(goals, key=lambda g: -goal_value(g))
