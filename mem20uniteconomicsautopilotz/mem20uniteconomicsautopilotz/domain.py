"""Unit economics autopilot: LTV, CAC, payback."""
def ltv(arpu, churn_rate, months=12):
    if churn_rate <= 0:
        return arpu * months
    return round(arpu / churn_rate, 4)


def cac(spend, customers):
    if customers == 0:
        return 0.0
    return round(spend / customers, 4)


def payback_months(cac_val, arpu):
    if arpu == 0:
        return float("inf")
    return round(cac_val / arpu, 4)


def ltv_cac_ratio(ltv_val, cac_val):
    if cac_val == 0:
        return float("inf")
    return round(ltv_val / cac_val, 4)


def economics_health(metrics):
    return {"ltv": metrics.get("ltv"), "cac": metrics.get("cac"), "ratio": metrics.get("ratio")}
