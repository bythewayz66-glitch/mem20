"""Product-led growth simulator: funnels, virality, retention."""
import random


def funnel(users, stages):
    counts = [users]
    for s in stages:
        rate = s.get("conversion", 0.5)
        counts.append(int(counts[-1]*rate))
    return counts


def viral_coefficient(invites_per_user, conversion_rate):
    return round(invites_per_user * conversion_rate, 4)


def retention_curve(users, churn_rate, periods=6):
    out = [users]
    for _ in range(periods):
        out.append(int(out[-1]*(1-churn_rate)))
    return out


def growth_score(metrics):
    # composite
    k = metrics.get("viral_k", 0)
    conv = metrics.get("conversion", 0)
    ret = metrics.get("retention", 0)
    return round((k + conv + ret)/3, 4)


def simulate(params, seed=0):
    rng = random.Random(seed)
    users = params.get("starting_users", 100)
    k = viral_coefficient(params.get("invites", 2), params.get("invite_conv", 0.1))
    growth = users * (1 + k)
    return {"starting": users, "viral_k": k, "after_viral": int(growth)}
