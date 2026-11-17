#!/usr/bin/env python3
"""pricing_model_v4.py — mem20 pricing model (v4 draft)

Models the $2,400 Starter tier with a 15% volume cap and its P&L drag.
This module is deterministic and dependency-free so it can be run in CI,
audited in code review, and used as a source for docs/pricing artifacts.

Notes:
- This is a planning/pricing model, not a billing system.
- All figures are explicit inputs/assumptions; no hidden defaults.
- "Volume cap" is modeled as a cap on the share of total account volume
  (mix) that Starter can represent in the blended book.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List
import json


@dataclass(frozen=True)
class Tier:
    name: str
    annual_price: float
    annual_cogs: float
    share: float  # share of account volume/mix (0..1)

    @property
    def annual_margin(self) -> float:
        return self.annual_price - self.annual_cogs

    @property
    def annual_margin_pct(self) -> float:
        if self.annual_price == 0:
            return 0.0
        return self.annual_margin / self.annual_price


@dataclass(frozen=True)
class PortfolioResult:
    tiers: List[Tier]
    blended_price: float
    blended_cogs: float
    blended_margin: float
    blended_margin_pct: float
    starter_share: float
    starter_volume_cap: float
    cap_binding: bool
    unconstrained_blended_price: float
    unconstrained_blended_margin: float
    blended_price_delta_vs_unconstrained: float
    blended_margin_delta_vs_unconstrained: float
    blended_margin_delta_pct_vs_unconstrained: float


def _validate_shares(tiers: List[Tier]) -> None:
    total = sum(t.share for t in tiers)
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"tier shares must sum to 1.0, got {total:.12f}")
    for t in tiers:
        if t.share < 0:
            raise ValueError(f"tier share cannot be negative: {t.name}={t.share}")


def blend(tiers: List[Tier]) -> Dict[str, float]:
    _validate_shares(tiers)
    blended_price = sum(t.annual_price * t.share for t in tiers)
    blended_cogs = sum(t.annual_cogs * t.share for t in tiers)
    blended_margin = blended_price - blended_cogs
    blended_margin_pct = (blended_margin / blended_price) if blended_price else 0.0
    return {
        "blended_price": blended_price,
        "blended_cogs": blended_cogs,
        "blended_margin": blended_margin,
        "blended_margin_pct": blended_margin_pct,
    }


def apply_starter_volume_cap(
    tiers: List[Tier],
    starter_name: str = "Starter",
    cap: float = 0.15,
) -> List[Tier]:
    """Cap Starter share at `cap` and redistribute excess proportionally
    across non-Starter tiers (preserving their relative mix).
    """
    if not (0.0 < cap <= 1.0):
        raise ValueError("cap must be in (0, 1]")
    by_name = {t.name: t for t in tiers}
    if starter_name not in by_name:
        raise ValueError(f"missing tier: {starter_name}")
    starter = by_name[starter_name]
    if starter.share <= cap:
        return list(tiers)

    excess = starter.share - cap
    others = [t for t in tiers if t.name != starter_name]
    other_total = sum(t.share for t in others)
    if other_total <= 0:
        raise ValueError("cannot redistribute excess when non-Starter share is zero")

    adjusted: List[Tier] = []
    for t in tiers:
        if t.name == starter_name:
            adjusted.append(Tier(t.name, t.annual_price, t.annual_cogs, cap))
        else:
            adjusted.append(
                Tier(
                    t.name,
                    t.annual_price,
                    t.annual_cogs,
                    t.share + excess * (t.share / other_total),
                )
            )
    _validate_shares(adjusted)
    return adjusted


def model_portfolio(
    tiers: List[Tier],
    starter_name: str = "Starter",
    starter_volume_cap: float = 0.15,
) -> PortfolioResult:
    unconstrained = blend(tiers)
    capped_tiers = apply_starter_volume_cap(tiers, starter_name=starter_name, cap=starter_volume_cap)
    capped = blend(capped_tiers)

    starter_share = next(t.share for t in tiers if t.name == starter_name)
    price_delta = capped["blended_price"] - unconstrained["blended_price"]
    margin_delta = capped["blended_margin"] - unconstrained["blended_margin"]
    margin_delta_pct = (margin_delta / unconstrained["blended_margin"]) if unconstrained["blended_margin"] else 0.0

    return PortfolioResult(
        tiers=capped_tiers,
        blended_price=capped["blended_price"],
        blended_cogs=capped["blended_cogs"],
        blended_margin=capped["blended_margin"],
        blended_margin_pct=capped["blended_margin_pct"],
        starter_share=starter_share,
        starter_volume_cap=starter_volume_cap,
        cap_binding=starter_share > starter_volume_cap,
        unconstrained_blended_price=unconstrained["blended_price"],
        unconstrained_blended_margin=unconstrained["blended_margin"],
        blended_price_delta_vs_unconstrained=price_delta,
        blended_margin_delta_vs_unconstrained=margin_delta,
        blended_margin_delta_pct_vs_unconstrained=margin_delta_pct,
    )


def default_v4_assumptions() -> List[Tier]:
    """Default planning assumptions for v4.

    Starter is explicitly modeled at $2,400/year. COGS and non-Starter tiers are
    planning assumptions and should be replaced with measured finance inputs as
    they become available.
    """
    return [
        # $2,400 Starter tier (requested), low-margin entry tier
        Tier(name="Starter", annual_price=2400.0, annual_cogs=1800.0, share=0.25),
        # Illustrative higher tiers for blend/P&L drag modeling
        Tier(name="Team", annual_price=12000.0, annual_cogs=4200.0, share=0.45),
        Tier(name="Business", annual_price=36000.0, annual_cogs=10800.0, share=0.20),
        Tier(name="Enterprise", annual_price=96000.0, annual_cogs=24000.0, share=0.10),
    ]


def main() -> int:
    tiers = default_v4_assumptions()
    result = model_portfolio(tiers, starter_name="Starter", starter_volume_cap=0.15)

    print("mem20 pricing_model_v4")
    print("======================")
    print(f"Starter volume cap: {result.starter_volume_cap:.0%}")
    print(f"Input Starter share: {result.starter_share:.2%}")
    print(f"Cap binding: {result.cap_binding}")
    print()
    print("Capped portfolio tiers:")
    for t in result.tiers:
        print(
            f"- {t.name:10s} price=${t.annual_price:,.0f} cogs=${t.annual_cogs:,.0f} "
            f"share={t.share:.2%} margin=${t.annual_margin:,.0f} ({t.annual_margin_pct:.1%})"
        )
    print()
    print(f"Blended price (annual/account): ${result.blended_price:,.2f} (unconstrained ${result.unconstrained_blended_price:,.2f}, delta ${result.blended_price_delta_vs_unconstrained:,.2f})")
    print(f"Blended COGS  (annual/account): ${result.blended_cogs:,.2f}")
    print(f"Blended margin (annual/account): ${result.blended_margin:,.2f} ({result.blended_margin_pct:.2%})")
    print(f"Unconstrained blended margin:    ${result.unconstrained_blended_margin:,.2f}")
    print(f"Margin delta vs unconstrained:   ${result.blended_margin_delta_vs_unconstrained:,.2f} ({result.blended_margin_delta_pct_vs_unconstrained:.2%})")
    print("P&L note: with the default assumptions, capping low-price/low-margin Starter volume at 15% shifts mix to higher tiers, increasing blended margin but changing revenue mix; replace assumptions with measured finance inputs for decision use.")
    print()
    print("JSON:")
    payload = asdict(result)
    payload["tiers"] = [asdict(t) for t in result.tiers]
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
