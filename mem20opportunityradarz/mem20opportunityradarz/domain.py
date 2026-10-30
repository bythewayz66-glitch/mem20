"""Opportunity radar: scan signals, score, alert."""
import math, time


def scan(signals, threshold=0.5):
    return [s for s in signals if s.get("score", 0) >= threshold]


def score_opportunity(opp, context):
    base = opp.get("value", 0) * opp.get("probability", 0.5)
    urgency = context.get("urgency", 1.0)
    return round(base * urgency, 4)


def rank(opps, context):
    scored = [(score_opportunity(o, context), o) for o in opps]
    scored.sort(reverse=True)
    return [o for _, o in scored]


def alert(opps, threshold=0.7):
    return [o for o in opps if o.get("score", 0) >= threshold]


def radar_health(opps):
    return {"total": len(opps), "high": sum(1 for o in opps if o.get("score",0)>=0.7)}
