"""Autonomous deal desk: pricing, terms, approval, negotiation."""

from __future__ import annotations

import math
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


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


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("add-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "add-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
