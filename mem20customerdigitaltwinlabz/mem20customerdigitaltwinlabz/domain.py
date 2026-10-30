"""Customer digital twin lab: profile, behavior sim, prediction."""
import math, random


def build_twin(customer):
    return {
        "id": customer.get("id"),
        "demographics": customer.get("demographics", {}),
        "behavior": customer.get("behavior", {}),
        "preferences": customer.get("preferences", {}),
        "ltv": customer.get("ltv", 0),
    }


def simulate_behavior(twin, scenario):
    rng = random.Random(scenario.get("seed", 0))
    actions = []
    for _ in range(scenario.get("steps", 5)):
        if rng.random() < twin.get("behavior", {}).get("engagement", 0.5):
            actions.append("interact")
        else:
            actions.append("idle")
    return actions


def predict_churn(twin):
    engagement = twin.get("behavior", {}).get("engagement", 0.5)
    recency = twin.get("behavior", {}).get("recency_days", 30)
    score = (1 - engagement) * 0.5 + min(1.0, recency / 90.0) * 0.5
    return round(score, 4)


def recommend_action(twin):
    churn = predict_churn(twin)
    if churn > 0.7:
        return "retention_offer"
    if twin.get("ltv", 0) > 1000:
        return "upsell"
    return "nurture"


def twin_accuracy(twin, actual):
    # simple: compare predicted churn to actual churned
    pred = predict_churn(twin)
    actual_churned = 1.0 if actual.get("churned") else 0.0
    return round(1 - abs(pred - actual_churned), 4)
