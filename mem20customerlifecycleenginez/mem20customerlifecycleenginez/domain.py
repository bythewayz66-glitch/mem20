"""Customer lifecycle engine: stages, transitions, retention."""
import math


def lifecycle_stage(customer):
    days = customer.get("days_since_signup", 0)
    purchases = customer.get("purchases", 0)
    if days <= 7:
        return "onboarding"
    if purchases == 0:
        return "inactive"
    if purchases >= 5 and days <= 90:
        return "loyal"
    if days > 180 and purchases < 2:
        return "churned_risk"
    return "active"


def transition(customer, event):
    stage = lifecycle_stage(customer)
    if event == "purchase":
        return "active" if stage != "churned_risk" else "reactivated"
    if event == "support_ticket":
        return "at_risk"
    if event == "churn":
        return "churned"
    return stage


def retention_probability(customer):
    engagement = customer.get("engagement", 0.5)
    recency = customer.get("recency_days", 30)
    return round(min(1.0, engagement * (1 - recency / 180.0)), 4)


def lifetime_value(customer):
    avg_order = customer.get("avg_order_value", 0)
    freq = customer.get("purchase_frequency", 0)
    lifespan = customer.get("expected_lifespan_months", 12)
    return round(avg_order * freq * lifespan, 2)


def segment_customers(customers):
    segs = {"onboarding": [], "active": [], "loyal": [], "at_risk": [], "churned": []}
    for c in customers:
        s = lifecycle_stage(c)
        segs.setdefault(s, []).append(c.get("id"))
    return segs
