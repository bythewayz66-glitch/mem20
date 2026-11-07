"""Cross-subsystem wiring for mem20autonomousdealdeskz.

Six peers chosen for the autonomous deal desk job (pricing, terms, approval,
negotiation) — not a generic memory/focus/catalog/webhook template. Adapters
return computed values; failures reported, never fatal.
"""

from __future__ import annotations

import pathlib
import sys
from typing import Mapping, Sequence

__all__ = [
    "economics_model",
    "demand_signal",
    "partnership_fit",
    "approval_guardrail",
    "capability_routing",
    "pipeline_context",
    "probe",
]

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_PROJECTS = (
    "mem20businessmodelsimulatorz",
    "mem20demandforecastandcapacitybrainz",
    "mem20acquisitionandpartnershipscoutz",
    "mem20antiexploitationrewardshieldz",
    "mem20capabilitymarketplacez",
    "mem20autonomoussaleslaboratoryz",
)


def _bootstrap() -> None:
    for name in reversed(_PROJECTS):
        path = str(_REPO_ROOT / name)
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)
    root = str(_REPO_ROOT)
    if root not in sys.path:
        sys.path.append(root)


_bootstrap()


def economics_model(units: int, price: float, fixed: float, variable: float) -> dict:
    """Model deal economics (margin/profit/scenario)."""
    try:
        from mem20businessmodelsimulatorz.domain import margin, profit, revenue, scenario_sim

        rev = revenue(units, price)
        cst = fixed + variable * units
        prof = profit(rev, cst)
        mar = margin(rev, cst)
        scenarios = scenario_sim(max(1, units), price, fixed, variable, growth=0.05, periods=2)
        return {
            "ok": True,
            "subsystem": "mem20businessmodelsimulatorz",
            "revenue": rev,
            "profit": prof,
            "margin": mar,
            "scenario_periods": len(scenarios),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20businessmodelsimulatorz", "error": f"{type(exc).__name__}: {exc}"}


def demand_signal(observations: Sequence[float]) -> dict:
    """Forecast demand/capacity signal for pricing and volume terms."""
    try:
        from mem20demandforecastandcapacitybrainz.domain import DemandForecastAndCapacityBrain

        brain = DemandForecastAndCapacityBrain(alpha=0.3, window=max(5, len(observations) or 5))
        for v in (observations or [10, 12, 11, 13]):
            brain.observe(v)
        fc = brain.forecast(steps=1)
        cap = brain.capacity_for(service_level=0.95)
        return {
            "ok": True,
            "subsystem": "mem20demandforecastandcapacitybrainz",
            "point": fc.get("point"),
            "high": fc.get("high"),
            "capacity_headroom": cap,
            "n": fc.get("n"),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20demandforecastandcapacitybrainz", "error": f"{type(exc).__name__}: {exc}"}


def partnership_fit(acquirer: Mapping, target: Mapping) -> dict:
    """Score partnership/acquisition fit relevant to strategic deals."""
    try:
        from mem20acquisitionandpartnershipscoutz.domain import (
            rank_targets,
            strategic_fit,
            synergy_estimate,
            target_score,
        )

        criteria = {"weights": {"revenue": 0.5, "growth": 0.5}, "targets": {"revenue": 1000, "growth": 0.2}}
        tgt = {**{"id": "tgt", "revenue": 500, "growth": 0.15, "markets": ["saas"], "tech": ["api"]}, **dict(target)}
        acq = {**{"id": "acq", "revenue": 5000, "markets": ["saas"], "tech": ["api", "ml"]}, **dict(acquirer)}
        if not isinstance(tgt.get("markets"), (list, set, tuple)): tgt["markets"] = ["saas"]
        if not isinstance(tgt.get("tech"), (list, set, tuple)): tgt["tech"] = ["api"]
        if not isinstance(acq.get("markets"), (list, set, tuple)): acq["markets"] = ["saas"]
        if not isinstance(acq.get("tech"), (list, set, tuple)): acq["tech"] = ["api"]
        score = target_score(tgt, criteria)
        fit = strategic_fit(acq, tgt)
        ranked = rank_targets([tgt, {"id": "alt", "revenue": 100, "growth": 0.05, "markets": ["other"], "tech": ["x"]}], criteria)
        synergy = synergy_estimate(acq, tgt)
        return {
            "ok": True,
            "subsystem": "mem20acquisitionandpartnershipscoutz",
            "target_score": float(score),
            "strategic_fit": float(fit),
            "ranked_count": len(ranked) if isinstance(ranked, list) else 0,
            "synergy": float(synergy) if synergy is not None else 0.0,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20acquisitionandpartnershipscoutz", "error": f"{type(exc).__name__}: {exc}"}


def approval_guardrail(claimed_reward: float, state: Mapping, progress_evidence: bool | None = None) -> dict:
    """Corroborate approval/action against exploitation (guardrail)."""
    try:
        from mem20antiexploitationrewardshieldz.domain import RewardShield

        shield = RewardShield(corroboration_tolerance=1.0, window=5, hard_clamp=1.0)
        result = shield.evaluate(claimed_reward, dict(state), progress_evidence=progress_evidence)
        ratio = shield.exploit_ratio()
        return {
            "ok": True,
            "subsystem": "mem20antiexploitationrewardshieldz",
            "paid": result.get("paid"),
            "reason": result.get("reason"),
            "exploit_ratio": ratio,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20antiexploitationrewardshieldz", "error": f"{type(exc).__name__}: {exc}"}


def capability_routing(key: str, capabilities: Sequence[str]) -> dict:
    """Route deal to a capability/provider via consistent hashing marketplace."""
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace

        market = CapabilityMarketplace(replicas=32)
        caps = list(capabilities) or ["pricing", "legal", "fulfillment"]
        for c in caps:
            market.add(c)
        owner = market.locate(key)
        dist = market.distribution(keys=100)
        return {
            "ok": True,
            "subsystem": "mem20capabilitymarketplacez",
            "owner": owner,
            "capabilities": len(caps),
            "distribution_keys": sum(dist.values()) if hasattr(dist, "values") else 100,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20capabilitymarketplacez", "error": f"{type(exc).__name__}: {exc}"}


def pipeline_context(leads: Sequence[Mapping]) -> dict:
    """Sales pipeline value/conversion context for deal desk."""
    try:
        from mem20autonomoussaleslaboratoryz.domain import (
            conversion_probability,
            pipeline_value,
            segment_leads,
        )

        items = [dict(l) for l in leads] or [{"deal_value": 5000, "budget": 3000, "authority": True, "need": True, "timeline_days": 20, "touches": 2}]
        value = pipeline_value(items)
        conv = conversion_probability(items[0], items[0].get("touches", 1))
        segments = segment_leads(items)
        return {
            "ok": True,
            "subsystem": "mem20autonomoussaleslaboratoryz",
            "pipeline_value": value,
            "conversion_probability": conv,
            "segments": {k: len(v) for k, v in segments.items()},
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20autonomoussaleslaboratoryz", "error": f"{type(exc).__name__}: {exc}"}


def probe() -> dict:
    """Probe all six deal-desk peers with safe calls."""
    checks = {
        "economics_model": economics_model(100, 10.0, 200.0, 2.0),
        "demand_signal": demand_signal([10, 12, 11, 13, 14]),
        "partnership_fit": partnership_fit({"id": "us"}, {"id": "them", "market": 0.7, "tech": 0.6}),
        "approval_guardrail": approval_guardrail(1.0, {"deal": "signed"}, progress_evidence=True),
        "capability_routing": capability_routing("deal-1", ["pricing", "legal"]),
        "pipeline_context": pipeline_context([{"deal_value": 5000, "budget": 3000, "authority": True, "need": True, "timeline_days": 20, "touches": 2}]),
    }
    return {"ok": all(v.get("ok") for v in checks.values()), "checks": checks}
