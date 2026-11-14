"""Customer lifecycle engine: stages, transitions, retention, with estate report."""
from __future__ import annotations
import math
from . import ecosystem
__all__=["lifecycle_stage","transition","retention_probability","lifetime_value","segment_customers","lifecycle_report","probe","estate_context"]

def lifecycle_stage(customer):
    days = customer.get("days_since_signup", 0); purchases = customer.get("purchases", 0)
    if days <= 7: return "onboarding"
    if purchases == 0: return "inactive"
    if purchases >= 5 and days <= 90: return "loyal"
    if days > 180 and purchases < 2: return "churned_risk"
    return "active"

def transition(customer, event):
    stage = lifecycle_stage(customer)
    if event == "purchase": return "active" if stage != "churned_risk" else "reactivated"
    if event == "support_ticket": return "at_risk"
    if event == "churn": return "churned"
    return stage

def retention_probability(customer):
    engagement = customer.get("engagement", 0.5); recency = customer.get("recency_days", 30)
    return round(min(1.0, engagement * (1 - recency / 180.0)), 4)

def lifetime_value(customer):
    avg_order = customer.get("avg_order_value", 0); freq = customer.get("purchase_frequency", 0); lifespan = customer.get("expected_lifespan_months", 12)
    return round(avg_order * freq * lifespan, 2)

def segment_customers(customers):
    segs = {"onboarding": [], "active": [], "loyal": [], "at_risk": [], "churned": []}
    for c in customers: s = lifecycle_stage(c); segs.setdefault(s, []).append(c.get("id"))
    return segs

def lifecycle_report(customer=None):
    customer = customer or {"id":"c1","days_since_signup":30,"purchases":3,"engagement":0.7,"recency_days":10,"avg_order_value":50,"purchase_frequency":2,"expected_lifespan_months":12,"tenure_months":6,"spend":150}
    stage=lifecycle_stage(customer); ret=retention_probability(customer); ltv=lifetime_value(customer)
    peers={
        "business_value": ecosystem.business_value(ltv),
        "pipeline_signal": ecosystem.pipeline_signal(max(1,ltv)),
        "loyalty_context": ecosystem.loyalty_context(["core","pro"]),
        "demand_signal": ecosystem.demand_signal([10,12,11,13,14]),
        "lifecycle_events": ecosystem.lifecycle_events("lifecycle.report", {"id":customer.get("id"),"stage":stage,"ltv":ltv}),
        "growth_partnerships": ecosystem.growth_partnerships(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"stage":stage,"retention":ret,"ltv":ltv,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=lifecycle_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
