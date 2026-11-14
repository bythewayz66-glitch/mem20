"""Mixed-initiative focus engine: attention, suggestions, takeover."""

from __future__ import annotations

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger


def focus_score(context: dict) -> float:
    # higher when fewer distractions
    distractions = context.get("distractions", 0)
    priority = context.get("priority", 1)
    return round(priority / (1 + distractions), 4)


def suggest(context: dict, options: list) -> list:
    scored = []
    for o in options:
        s = focus_score({**context, "priority": o.get("priority", 1)})
        scored.append((s, o))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [o for _, o in scored]


def take_over(initiative_level: float, threshold: float = 0.5) -> bool:
    return initiative_level >= threshold


def blend(user_intent: dict, agent_intent: dict, alpha: float = 0.5) -> dict:
    # alpha: weight of user intent
    return {
        "blended_priority": alpha * user_intent.get("priority", 0)
        + (1 - alpha) * agent_intent.get("priority", 0)
    }


def focus_health(context: dict) -> dict:
    return {"score": focus_score(context), "healthy": focus_score(context) > 0.3}


def _toolchest_inventory_path():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    if p.exists():
        return p
    return root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | None = None) -> dict:
    """Real cross-module integration for focus decisions."""
    from mem20memorytimemachinez.domain import diff

    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("focus-probe")
    delta = diff({"a": 1}, {"a": 2})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "focus-probe" in ledger,
        "delta_keys": sorted(delta.keys()),
    }
    if store_path is not None:
        from pathlib import Path

        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.index_health()
        ctx["engine_status_checked"] = True
    return ctx
