"""Predictive recall engine: predict what user will need next, with estate report."""
from __future__ import annotations
import math
from . import ecosystem
__all__=["predict_next","recall_score","prefetch","cache_hit_rate","recall_health","recall_report","probe","estate_context"]

def predict_next(history, candidates):
    from collections import Counter
    c = Counter(history)
    scored = [(c.get(cand, 0), cand) for cand in candidates]
    scored.sort(reverse=True)
    return [c for _, c in scored]

def recall_score(item, context):
    recency = context.get("recency", {}).get(item, 0)
    frequency = context.get("frequency", {}).get(item, 0)
    return round(0.6*frequency + 0.4*recency, 4)

def prefetch(predictions, k=3):
    return predictions[:k]

def cache_hit_rate(hits, total):
    if total == 0: return 0.0
    return round(hits / total, 4)

def recall_health(predictions):
    return {"predictions": len(predictions)}

def recall_report(history=None, candidates=None):
    history = history or ["a","b","a","c","a"]
    candidates = candidates or ["a","b","c","d"]
    preds=predict_next(history,candidates); pf=prefetch(preds,2); rate=cache_hit_rate(3,5)
    peers={
        "causal_routing": ecosystem.causal_routing({"frequency":1},{"frequency":1}),
        "context_compression": ecosystem.context_compression(" ".join(history)),
        "recall_events": ecosystem.recall_events("recall.report", {"predictions":len(preds),"prefetch":len(pf)}),
        "focus_context": ecosystem.focus_context({"priority":1,"distractions":0}),
        "capability_routing": ecosystem.capability_routing("recall", ["predict","prefetch","score"]),
        "demand_forecast": ecosystem.demand_forecast([1,2,2,3,4]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"predictions":preds,"prefetch":pf,"cache_hit_rate":rate,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=recall_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
