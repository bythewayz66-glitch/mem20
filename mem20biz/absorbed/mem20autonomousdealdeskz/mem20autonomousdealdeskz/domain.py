"""Autonomous deal desk: pricing, terms, approval, negotiation, and estate report."""

from __future__ import annotations

import math

from . import ecosystem

__all__ = [
    "price_deal",
    "terms_score",
    "approval_required",
    "negotiate_round",
    "deal_health",
    "deal_report",
    "probe",
    "estate_context",
]


def price_deal(product, customer, discount_cap=0.2):
    base = product.get("price", 0)
    volume = customer.get("volume", 1)
    volume_discount = min(discount_cap, (volume / 1000.0) * 0.05)
    price = base * (1 - volume_discount)
    return round(price, 2)


def terms_score(terms):
    score = 0.0
    if terms.get("payment_days", 30) <= 30:
        score += 0.3
    if terms.get("contract_months", 12) >= 12:
        score += 0.4
    if terms.get("auto_renew"):
        score += 0.3
    return round(score, 3)


def approval_required(deal_value, threshold=10000):
    return deal_value > threshold


def negotiate_round(current_price, counter_offer, rounds_left):
    if rounds_left <= 0:
        return current_price
    midpoint = (current_price + counter_offer) / 2
    return round(midpoint, 2)


def deal_health(deal):
    score = 0.0
    if deal.get("signed"):
        score += 0.4
    if deal.get("paid"):
        score += 0.3
    if deal.get("renewed"):
        score += 0.3
    return round(score, 3)


def deal_report(product=None, customer=None, terms=None, deal=None, demand_obs=None):
    """Run deal desk ops and collect 6 subsystem-specific peer judgements."""
    product = product or {"price": 1000}
    customer = customer or {"volume": 500}
    terms = terms or {"payment_days": 15, "contract_months": 12, "auto_renew": True}
    deal = deal or {"signed": True, "paid": False, "deal_value": 9500}
    price = price_deal(product, customer)
    tscore = terms_score(terms)
    needs_approval = approval_required(deal.get("deal_value", price), threshold=10000)
    negotiated = negotiate_round(price, price * 0.9, 2)
    health = deal_health(deal)
    peers = {
        "economics_model": ecosystem.economics_model(customer.get("volume", 100), max(0.01, price), 500.0, 2.0),
        "demand_signal": ecosystem.demand_signal(demand_obs or [10, 12, 11, 13, 14]),
        "partnership_fit": ecosystem.partnership_fit({"id": "seller"}, {"id": "buyer"}),
        "approval_guardrail": ecosystem.approval_guardrail(1.0, {"deal_value": deal.get("deal_value", price), "terms_score": tscore}, progress_evidence=not needs_approval),
        "capability_routing": ecosystem.capability_routing(f"deal-{int(deal.get('deal_value', price))}", ["pricing", "legal", "fulfillment"]),
        "pipeline_context": ecosystem.pipeline_context([{"deal_value": deal.get("deal_value", price), "budget": int(price), "authority": True, "need": True, "timeline_days": terms.get("payment_days", 30), "touches": 2}]),
    }
    return {
        "ok": all(v.get("ok") for v in peers.values()),
        "price": price,
        "terms_score": tscore,
        "approval_required": needs_approval,
        "negotiated_price": negotiated,
        "deal_health": health,
        "peers": peers,
    }


def probe():
    return ecosystem.probe()


def estate_context(store_path: str | None = None):
    _ = store_path
    report = deal_report()
    return {
        "engine_status_checked": True,
        "peer_count": len(report.get("peers", {})),
        "peers_ok": report.get("ok"),
        "checks": report.get("peers", {}),
    }
