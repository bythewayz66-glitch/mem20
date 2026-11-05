"""Live model fusion: combine model outputs dynamically."""

from __future__ import annotations

from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def fuse(models, weights=None):
    if not models:
        return None
    weights = weights or [1.0 / len(models)] * len(models)
    keys = set()
    for m in models:
        keys.update(m.get("outputs", {}).keys())
    out = {}
    for k in keys:
        vals = [m.get("outputs", {}).get(k, 0) for m in models]
        out[k] = sum(v * w for v, w in zip(vals, weights))
    return {"fused": out, "models": len(models)}


def weight_by_confidence(models):
    confs = [m.get("confidence", 0.5) for m in models]
    s = sum(confs) or 1
    return [c / s for c in confs]


def select_best(models, metric="accuracy"):
    if not models:
        return None
    return max(models, key=lambda m: m.get(metric, 0))


def ensemble_vote(predictions):
    from collections import Counter

    c = Counter(predictions)
    return c.most_common(1)[0][0] if c else None


def fusion_health(models):
    return {
        "count": len(models),
        "avg_confidence": round(sum(m.get("confidence", 0) for m in models) / max(1, len(models)), 4),
    }


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("fusion-probe")
    score = focus_score({"priority": 1, "distractions": 1})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "fusion-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.index_health()
        ctx["engine_status_checked"] = True
    return ctx
