"""Customer digital twin lab: profile, behavior sim, prediction, with estate report."""
from __future__ import annotations
import random
from . import ecosystem
__all__=["build_twin","simulate_behavior","predict_churn","recommend_action","twin_accuracy","twin_report","probe","estate_context"]

def build_twin(customer):
    return {"id": customer.get("id"),"demographics": customer.get("demographics", {}),"behavior": customer.get("behavior", {}),"preferences": customer.get("preferences", {}),"ltv": customer.get("ltv", 0)}
def simulate_behavior(twin, scenario):
    rng = random.Random(scenario.get("seed", 0)); actions = []
    for _ in range(scenario.get("steps", 5)):
        actions.append("interact" if rng.random() < twin.get("behavior", {}).get("engagement", 0.5) else "idle")
    return actions
def predict_churn(twin):
    engagement = twin.get("behavior", {}).get("engagement", 0.5); recency = twin.get("behavior", {}).get("recency_days", 30)
    return round((1 - engagement) * 0.5 + min(1.0, recency / 90.0) * 0.5, 4)
def recommend_action(twin):
    churn = predict_churn(twin)
    if churn > 0.7: return "retention_offer"
    if twin.get("ltv", 0) > 1000: return "upsell"
    return "nurture"
def twin_accuracy(twin, actual):
    pred = predict_churn(twin); actual_churned = 1.0 if actual.get("churned") else 0.0
    return round(1 - abs(pred - actual_churned), 4)

def twin_report(customer=None):
    customer = customer or {"id":"c1","ltv":1200,"behavior":{"engagement":0.6,"recency_days":10},"preferences":{"products":["core"]},"demographics":{},"tenure_months":8,"spend":200}
    twin=build_twin(customer); actions=simulate_behavior(twin,{"seed":1,"steps":3}); churn=predict_churn(twin); action=recommend_action(twin)
    peers={
        "lifecycle_signal": ecosystem.lifecycle_signal(customer),
        "counterfactual_scenarios": ecosystem.counterfactual_scenarios({"engagement":twin["behavior"].get("engagement",0.5)}),
        "demand_signal": ecosystem.demand_signal([5,6,7,6,8]),
        "loyalty_context": ecosystem.loyalty_context(twin.get("preferences",{}).get("products",["core"])),
        "twin_events": ecosystem.twin_events("twin.report", {"id":twin["id"],"churn":churn,"action":action}),
        "capability_routing": ecosystem.capability_routing(twin["id"] or "c1", ["predict","simulate","recommend"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"churn":churn,"recommended_action":action,"actions":actions,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=twin_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
