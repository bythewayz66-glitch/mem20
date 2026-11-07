"""Autonomous micro-SaaS foundry: idea scoring, MVP spec, launch plan."""

from __future__ import annotations

import math
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def score_idea(idea):
    market = idea.get("market_size", 0)
    competition = idea.get("competition", 5)
    effort = idea.get("effort", 5)
    score = (market / 100.0) * (1 / max(1, competition)) * (1 / max(1, effort))
    return round(min(1.0, score), 4)


def mvp_spec(idea):
    return {
        "name": idea.get("name"),
        "core_features": idea.get("features", [])[:3],
        "tech_stack": idea.get("stack", "python+react"),
        "timeline_weeks": max(2, idea.get("effort", 4)),
    }


def launch_plan(spec):
    return {
        "phases": ["build", "beta", "launch", "growth"],
        "beta_users": 50,
        "launch_channels": ["producthunt", "twitter", "reddit"],
        "pricing": spec.get("price", 9),
    }


def revenue_projection(users, price, churn=0.05):
    mrr = users * price
    annual = mrr * 12 * (1 - churn)
    return {"mrr": mrr, "arr": round(annual, 2)}


def idea_ranking(ideas):
    scored = [(score_idea(i), i) for i in ideas]
    scored.sort(reverse=True)
    return scored


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("amsf-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "amsf-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
