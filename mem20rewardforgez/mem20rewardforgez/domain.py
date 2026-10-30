"""Reward forge: craft reward functions for RL."""
import math


def linear_reward(state, weights):
    return sum(weights.get(k, 0) * state.get(k, 0) for k in weights)


def shaped_reward(base, shaping):
    return base + shaping


def normalize(rewards):
    if not rewards:
        return []
    mn, mx = min(rewards), max(rewards)
    rng = mx - mn or 1
    return [(r - mn) / rng for r in rewards]


def reward_health(rewards):
    if not rewards:
        return {"count": 0}
    return {"count": len(rewards), "mean": sum(rewards)/len(rewards), "min": min(rewards), "max": max(rewards)}
