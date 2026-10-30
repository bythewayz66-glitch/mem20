"""GOAP agent designer: goals, actions, planning."""
import math


def plan(actions, start_state, goal_state):
    # simple: find actions whose effects move toward goal
    plan = []
    state = dict(start_state)
    remaining = dict(goal_state)
    # greedy
    available = list(actions)
    while remaining and available:
        best = None
        best_gain = 0
        for a in available:
            gain = sum(1 for k, v in remaining.items() if a.get("effects", {}).get(k) == v)
            if gain > best_gain:
                best_gain = gain
                best = a
        if best is None or best_gain == 0:
            break
        plan.append(best.get("name"))
        for k, v in best.get("effects", {}).items():
            if k in remaining and remaining[k] == v:
                del remaining[k]
        available.remove(best)
    return plan


def action_cost(action):
    return action.get("cost", 1)


def heuristic(state, goal):
    return sum(1 for k, v in goal.items() if state.get(k) != v)


def validate_plan(plan, actions):
    names = {a.get("name") for a in actions}
    return all(p in names for p in plan)
