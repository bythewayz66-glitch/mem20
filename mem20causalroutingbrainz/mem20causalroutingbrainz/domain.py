"""Causal routing brain: causal inference for routing decisions."""

from __future__ import annotations

import math
import random
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def causal_effect(treatment_outcomes, control_outcomes):
    """Average treatment effect."""
    if not treatment_outcomes or not control_outcomes:
        return 0.0
    return round(sum(treatment_outcomes) / len(treatment_outcomes) - sum(control_outcomes) / len(control_outcomes), 4)


def route_by_cause(features, causal_weights):
    """Route based on causal weights."""
    score = 0.0
    for k, w in causal_weights.items():
        score += features.get(k, 0) * w
    return score


def confounder_adjust(raw_effect, confounder_strength):
    return round(raw_effect * (1 - confounder_strength), 4)


def intervention_value(baseline, intervention_outcome):
    return round(intervention_outcome - baseline, 4)


def causal_graph(edges):
    """Build adjacency for causal graph."""
    graph = {}
    for src, dst in edges:
        graph.setdefault(src, []).append(dst)
    return graph


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("crb-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "crb-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
