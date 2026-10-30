"""Elasticity-fitted adaptive pricing with revenue/margin objectives."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Sequence


def _fit(points: Sequence[tuple[float, float]]) -> tuple[float, float]:
    pts = [(float(p), float(q)) for p, q in points if float(p) > 0 and float(q) >= 0]
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


def recommend_price(
    observations: Sequence[tuple[float, float]],
    *,
    objective: str = "revenue",
    cost: float = 0.0,
    price_floor: float = 0.01,
    price_ceiling: float = 1000.0,
    steps: int = 200,
) -> dict[str, Any]:
    intercept, elasticity = _fit(observations)

    def demand(p: float) -> float:
        p = max(1e-9, float(p))
        return math.exp(intercept + elasticity * math.log(p))

    lo = max(price_floor, 1e-6)
    hi = max(price_ceiling, price_floor * 2)
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
        "demand_character": "elastic" if abs(elasticity) > 1 else "inelastic",
        "observations_used": len(observations),
    }


@dataclass
class PricingObservation:
    price: float
    quantity: float
    ts: float = 0.0
    sku: str = ""


@dataclass
class PricingBrain:
    observations: list[PricingObservation] = field(default_factory=list)
    cost: float = 0.0
    price_floor: float = 0.01
    price_ceiling: float = 1000.0
    objective: str = "revenue"

    def observe(self, price: float, quantity: float, sku: str = "", ts: float = 0.0) -> None:
        self.observations.append(
            PricingObservation(price=price, quantity=quantity, sku=sku, ts=ts)
        )

    def recommend(self, sku: str | None = None) -> dict[str, Any]:
        pts = [
            (o.price, o.quantity)
            for o in self.observations
            if sku is None or o.sku == sku
        ]
        return recommend_price(
            pts,
            objective=self.objective,
            cost=self.cost,
            price_floor=self.price_floor,
            price_ceiling=self.price_ceiling,
        )

    def elasticity(self, sku: str | None = None) -> float:
        return float(self.recommend(sku)["elasticity"])
