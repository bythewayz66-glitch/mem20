"""Acquisition & partnerships scout: target scoring, fit analysis, outreach."""
import math


def target_score(company, criteria):
    """Score an acquisition target against criteria (0..1)."""
    score = 0.0
    weights = criteria.get("weights", {})
    for k, w in weights.items():
        val = company.get(k, 0)
        target = criteria.get("targets", {}).get(k, 1)
        if isinstance(target, (int, float)) and target:
            ratio = min(1.0, float(val) / float(target)) if target > 0 else 0.0
            score += w * ratio
    return round(score, 4)


def strategic_fit(acquirer, target):
    """Compute strategic fit score between two companies."""
    overlap = set(acquirer.get("markets", [])) & set(target.get("markets", []))
    tech_overlap = set(acquirer.get("tech", [])) & set(target.get("tech", []))
    score = len(overlap) * 0.3 + len(tech_overlap) * 0.4
    size_ratio = target.get("revenue", 1) / max(1, acquirer.get("revenue", 1))
    if 0.05 <= size_ratio <= 0.5:
        score += 0.3
    return round(min(1.0, score), 4)


def rank_targets(targets, criteria):
    """Rank targets by score desc."""
    scored = [(target_score(t, criteria), t) for t in targets]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def outreach_priority(target, criteria):
    """Determine outreach priority tier."""
    s = target_score(target, criteria)
    if s >= 0.8:
        return "high"
    if s >= 0.5:
        return "medium"
    return "low"


def synergy_estimate(acquirer, target):
    """Rough synergy estimate (revenue uplift)."""
    return round(target.get("revenue", 0) * 0.15 * strategic_fit(acquirer, target), 2)
