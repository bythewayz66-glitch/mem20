"""Live model fusion: combine model outputs dynamically."""
import math


def fuse(models, weights=None):
    if not models:
        return None
    weights = weights or [1.0/len(models)]*len(models)
    # numeric fusion
    keys = set()
    for m in models:
        keys.update(m.get("outputs", {}).keys())
    out = {}
    for k in keys:
        vals = [m.get("outputs", {}).get(k, 0) for m in models]
        out[k] = sum(v*w for v, w in zip(vals, weights))
    return {"fused": out, "models": len(models)}


def weight_by_confidence(models):
    confs = [m.get("confidence", 0.5) for m in models]
    s = sum(confs) or 1
    return [c/s for c in confs]


def select_best(models, metric="accuracy"):
    if not models:
        return None
    return max(models, key=lambda m: m.get(metric, 0))


def ensemble_vote(predictions):
    from collections import Counter
    c = Counter(predictions)
    return c.most_common(1)[0][0] if c else None


def fusion_health(models):
    return {"count": len(models), "avg_confidence": round(sum(m.get("confidence",0) for m in models)/max(1,len(models)),4)}
