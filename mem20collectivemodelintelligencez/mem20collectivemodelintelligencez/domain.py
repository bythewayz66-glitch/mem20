"""Collective model intelligence: ensemble, voting, aggregation."""

from __future__ import annotations

import math
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def ensemble_predict(predictions, weights=None):
    if not predictions:
        return None
    if weights is None:
        weights = [1.0] * len(predictions)
    total_w = sum(weights)
    if total_w == 0:
        return None
    if isinstance(predictions[0], (int, float)):
        return round(sum(p * w for p, w in zip(predictions, weights)) / total_w, 4)
    votes = {}
    for p, w in zip(predictions, weights):
        votes[p] = votes.get(p, 0) + w
    return max(votes, key=votes.get)


def diversity_score(models_predictions):
    """Measure diversity among model predictions."""
    if len(models_predictions) < 2:
        return 0.0
    disagreements = 0
    total = 0
    for i in range(len(models_predictions)):
        for j in range(i + 1, len(models_predictions)):
            total += 1
            if models_predictions[i] != models_predictions[j]:
                disagreements += 1
    return round(disagreements / max(1, total), 4)


def knowledge_distill(teacher_preds, student_preds, temperature=2.0):
    """KL-like distillation loss (simplified)."""
    loss = 0.0
    for t, s in zip(teacher_preds, student_preds):
        loss += (t - s) ** 2
    return round(loss / max(1, len(teacher_preds)), 4)


def aggregate_confidence(confidences):
    if not confidences:
        return 0.0
    return round(sum(confidences) / len(confidences), 4)


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("cmi-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "cmi-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
