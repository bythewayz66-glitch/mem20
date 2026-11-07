"""Autonomous sales laboratory: lead scoring, outreach, conversion."""

from __future__ import annotations

import math
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def lead_score(lead):
    score = 0.0
    if lead.get("budget", 0) > 1000:
        score += 0.3
    if lead.get("authority"):
        score += 0.3
    if lead.get("need"):
        score += 0.2
    if lead.get("timeline_days", 999) <= 30:
        score += 0.2
    return round(score, 3)


def outreach_message(lead, template):
    return {
        "to": lead.get("email"),
        "subject": template.get("subject", "Hello").format(name=lead.get("name", "")),
        "body": template.get("body", "").format(name=lead.get("name", "")),
    }


def conversion_probability(lead, touches):
    base = lead_score(lead)
    boost = min(0.3, touches * 0.05)
    return round(min(1.0, base + boost), 3)


def pipeline_value(leads):
    return round(sum(l.get("deal_value", 0) * conversion_probability(l, l.get("touches", 0)) for l in leads), 2)


def segment_leads(leads):
    hot = [l for l in leads if lead_score(l) >= 0.7]
    warm = [l for l in leads if 0.4 <= lead_score(l) < 0.7]
    cold = [l for l in leads if lead_score(l) < 0.4]
    return {"hot": hot, "warm": warm, "cold": cold}


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("asl-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "asl-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
