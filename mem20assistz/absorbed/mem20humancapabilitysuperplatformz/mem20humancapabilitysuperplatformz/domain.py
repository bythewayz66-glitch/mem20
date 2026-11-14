"""Human capability super-platform: skills, assessment, growth."""
import math


def assess(capability, evidence):
    score = 0.0
    for e in evidence:
        score += e.get("weight", 1) * e.get("value", 0)
    return round(min(1.0, score / max(1, len(evidence))), 4) if evidence else 0.0


def growth_plan(current, target):
    gaps = []
    for skill, lvl in target.items():
        cur = current.get(skill, 0)
        if cur < lvl:
            gaps.append({"skill": skill, "current": cur, "target": lvl, "delta": lvl - cur})
    return gaps


def capability_matrix(users, skills):
    matrix = {}
    for u in users:
        matrix[u.get("id")] = {s: u.get("skills", {}).get(s, 0) for s in skills}
    return matrix


def team_capability(matrix, skill):
    vals = [m.get(skill, 0) for m in matrix.values()]
    if not vals:
        return 0.0
    return round(sum(vals) / len(vals), 4)


def learning_recommendation(gaps):
    return sorted(gaps, key=lambda g: -g.get("delta", 0))
