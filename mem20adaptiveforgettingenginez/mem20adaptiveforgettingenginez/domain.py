"""Ebbinghaus forgetting curve with spaced reinforcement scheduling.

Option C: real domain logic for mem20adaptiveforgettingenginez.
"""
"""Ebbinghaus-style forgetting with spaced reinforcement.

Real behaviour: models per-item retention from the Ebbinghaus curve
R = exp(-t / S) where stability S grows with each successful review, decides
whether an item is retrievable under a threshold, and schedules the next
review. This is the classic spacing effect, computed rather than described.
"""
import math, time


def retention(elapsed_days, stability_days):
    """Fraction of the trace still retrievable after elapsed_days."""
    if stability_days <= 0:
        return 0.0
    return math.exp(-max(0.0, float(elapsed_days)) / float(stability_days))


def reinforce(stability_days, success=True, growth=1.8, decay=0.4):
    """Update stability after a review. Success widens the interval."""
    s = max(1e-6, float(stability_days))
    return s * (growth if success else decay)


def review_state(last_review_ts, stability_days, now_ts=None,
                 threshold=0.5):
    now_ts = time.time() if now_ts is None else now_ts
    elapsed = (now_ts - last_review_ts) / 86400.0
    r = retention(elapsed, stability_days)
    return {
        "elapsed_days": round(elapsed, 4),
        "stability_days": round(float(stability_days), 4),
        "retention": round(r, 6),
        # tolerance: exp(-ln2) evaluates to 0.4999999999999998, so a
        # value that is exactly at threshold was being called lapsed.
        "retrievable": bool(r >= threshold - 1e-9),
        "threshold": threshold,
        # next review lands exactly where retention decays to threshold
        "next_review_days": round(-math.log(threshold) * stability_days, 4)
        if threshold > 0 else None,
    }


def review_queue(items, now_ts=None, threshold=0.5, limit=20):
    """items: [{id, last_review_ts, stability_days}]. Most-lapsed first."""
    now_ts = time.time() if now_ts is None else now_ts
    scored = []
    for it in items:
        st = review_state(it["last_review_ts"], it.get("stability_days", 1.0),
                          now_ts, threshold)
        st["id"] = it.get("id")
        scored.append(st)
    scored.sort(key=lambda s: s["retention"])
    due = [s for s in scored if not s["retrievable"]]
    return {"due_count": len(due), "queue": due[:limit],
            "scheduled": len(scored) - len(due)}
