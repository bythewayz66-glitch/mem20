"""Apprenticeship runtime: skill tracking, mentorship, progression, evaluation."""
import math


def skill_level(xp):
    levels = [0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500]
    lvl = 0
    for i, t in enumerate(levels):
        if xp >= t:
            lvl = i
    return lvl


def mentor_match(apprentice, mentors):
    """Match apprentice to best mentor by skill gap."""
    best = None
    best_score = -1
    for m in mentors:
        overlap = len(set(apprentice.get("skills", [])) & set(m.get("skills", [])))
        score = overlap + m.get("experience", 0) * 0.1
        if score > best_score:
            best_score = score
            best = m
    return best


def evaluate_task(task, submission):
    """Evaluate an apprentice's task submission."""
    expected = task.get("expected", {})
    score = 0
    total = len(expected)
    for k, v in expected.items():
        if submission.get(k) == v:
            score += 1
    return {"score": score, "total": total, "pass": score >= total * 0.7}


def progression_plan(current_level, target_level):
    """Plan skill progression steps."""
    steps = []
    for lvl in range(current_level + 1, target_level + 1):
        steps.append({"level": lvl, "xp_required": lvl * 100 * (lvl + 1) // 2})
    return steps


def mentorship_hours(mentor, apprentice, weeks):
    """Compute recommended mentorship hours."""
    base = 2.0
    gap = abs(mentor.get("level", 0) - apprentice.get("level", 0))
    return round(base * (1 + gap * 0.2) * weeks, 1)
