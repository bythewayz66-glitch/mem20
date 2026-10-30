"""Predictive recall engine: predict what user will need next."""
import math


def predict_next(history, candidates):
    # score candidates by frequency in history
    from collections import Counter
    c = Counter(history)
    scored = []
    for cand in candidates:
        scored.append((c.get(cand, 0), cand))
    scored.sort(reverse=True)
    return [c for _, c in scored]


def recall_score(item, context):
    recency = context.get("recency", {}).get(item, 0)
    frequency = context.get("frequency", {}).get(item, 0)
    return round(0.6*frequency + 0.4*recency, 4)


def prefetch(predictions, k=3):
    return predictions[:k]


def cache_hit_rate(hits, total):
    if total == 0:
        return 0.0
    return round(hits / total, 4)


def recall_health(predictions):
    return {"predictions": len(predictions)}
