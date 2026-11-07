"""mem20selfz domain: self-model integration with 6 peers."""
from __future__ import annotations
from . import ecosystem
__all__=["self_report","probe","estate_context"]

def self_report():
    peers={
        "episodic_memory": ecosystem.episodic_memory("self state"),
        "context_compression": ecosystem.context_compression("self model context summary"),
        "causal_routing": ecosystem.causal_routing({"focus":1},{"focus":1}),
        "self_events": ecosystem.self_events("self.updated", {"ok":True}),
        "capability_routing": ecosystem.capability_routing("self", ["reflect","remember","report"]),
        "health_nervous": ecosystem.health_nervous(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"peers":peers}

def probe(): return ecosystem.probe()

def estate_context(store_path: str | None = None):
    """Probe the real mem20 estate modules plus 6 peer judgements (core API preserved)."""
    from pathlib import Path
    import mem20path
    from memory_engine import EngineConfig, MemoryEngine
    from mem20mixedinitiativefocusenginez.domain import focus_score
    from mem20sitemapz.policy import is_skipped_dir
    from mem20webhooksupernetworkz.domain import DeliveryLedger
    from toolchest.catalog import load_inventory

    root = Path(__file__).resolve().parents[2]
    inventory_path = root / "toolchest" / "inventory.json"
    if not inventory_path.exists():
        inventory_path = root / "toolchest" / "src" / "toolchest" / "inventory.json"
    inventory = load_inventory(inventory_path)
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("mem20selfz-work")
    scripts = mem20path.discover_scripts()
    focus = focus_score({"priority": 1, "distractions": 0})
    cache_skipped = is_skipped_dir("__pycache__")
    ctx = {
        "path_scripts": len(scripts),
        "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
        "work_recorded": "mem20selfz-work" in ledger,
        "focus_score": float(focus),
        "sitemap_skips_cache": cache_skipped,
    }
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        engine = MemoryEngine(config)
        ctx["engine_status_checked"] = engine.config is not None
    else:
        ctx["engine_status_checked"] = False
    r = self_report()
    ctx["peer_count"] = len(r.get("peers", {}))
    ctx["peers_ok"] = r.get("ok")
    ctx["checks"] = r.get("peers", {})
    return ctx
