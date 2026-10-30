"""Synthetic evaluator arena: agents evaluate each other."""
import random


def create_arena(agents):
    return {"agents": list(agents), "evaluations": [], "scores": {a: 0.0 for a in agents}}


def evaluate(arena, evaluator, subject, score):
    arena["evaluations"].append({"evaluator": evaluator, "subject": subject, "score": score})
    arena["scores"][subject] = arena["scores"].get(subject, 0) + score
    return arena


def leaderboard(arena):
    return sorted([{"agent": a, "score": s} for a, s in arena["scores"].items()], key=lambda r: -r["score"])


def arena_health(arena):
    return {"agents": len(arena["agents"]), "evaluations": len(arena["evaluations"])}
