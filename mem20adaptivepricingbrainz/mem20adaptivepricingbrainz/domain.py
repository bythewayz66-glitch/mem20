"""Elasticity-fitted adaptive pricing with revenue/margin objectives.

Option C: real domain logic for mem20adaptivepricingbrainz.
"""
"""Elasticity-driven adaptive pricing.

Real behaviour, not a roadmap-id switch: fits a demand curve from observed
price/quantity points, estimates point elasticity by log-log regression, and
recommends a price that maximises revenue (or margin) subject to a floor.
"""
import math


def _fit(points):
    """log-log OLS of quantity on price -> (intercept, slope=elasticity)."""
    pts = [(float(p), float(q)) for p, q in points
           if float(p) > 0 and float(q) >= 0]
    if len(pts) < 2:
        raise ValueError("need at least 2 observations with positive price")
    xs = [math.log(p) for p, _ in pts]
    ys = [math.log(q) if q > 0 else -30.0 for _, q in pts]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs)
    if denom < 1e-12:
        raise ValueError("degenerate: all prices identical")
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom
    return my - slope * mx, slope


def recommend_price(observations, objective="revenue", cost=0.0,
                    price_floor=0.01, price_ceiling=1000.0, steps=200):
    """Recommend a price from (price, quantity) observations.

    objective: 'revenue' maximises p*q, 'margin' maximises (p-cost)*q.
    Returns the recommendation plus the fitted elasticity and its sign.
    """
    intercept, elasticity = _fit(observations)

    def demand(p):
        p = max(1e-9, float(p))
        return math.exp(intercept + elasticity * math.log(p))

    lo, hi = max(price_floor, 1e-6), max(price_ceiling, price_floor * 2)
    best_p, best_v = lo, -1e18
    for i in range(steps):
        p = lo + (hi - lo) * i / max(1, steps - 1)
        q = demand(p)
        v = p * q if objective == "revenue" else (p - cost) * q
        if v > best_v:
            best_v, best_p = v, p
    return {
        "recommended_price": round(best_p, 6),
        "objective": objective,
        "predicted_quantity": round(demand(best_p), 6),
        "objective_value": round(best_v, 6),
        "elasticity": round(elasticity, 6),
        "demand_character": ("elastic" if abs(elasticity) > 1 else "inelastic"),
        "observations_used": len(observations),
    }
