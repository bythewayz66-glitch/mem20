"""Visual agent blackboard: shared visual state for agents (6 peers)."""
from __future__ import annotations
import time
from . import ecosystem
__all__=["create_blackboard","post","read","clear","blackboard_health","blackboard_report","probe","estate_context"]

def create_blackboard(name):
    return {"name": name, "items": [], "agents": set()}

def post(bb, agent, item):
    bb["items"].append({"agent": agent, "item": item, "ts": time.time()})
    bb["agents"].add(agent)
    return bb

def read(bb, agent=None):
    if agent:
        return [i for i in bb["items"] if i["agent"] == agent]
    return list(bb["items"])

def clear(bb):
    bb["items"] = []
    return bb

def blackboard_health(bb):
    return {"items": len(bb["items"]), "agents": len(bb["agents"])}

def blackboard_report():
    bb=create_blackboard("r"); post(bb,"a1","item"); h=blackboard_health(bb)
    peers={
        "workcell_dispatch": ecosystem.workcell_dispatch(),
        "output_compile": ecosystem.output_compile(),
        "team_presence": ecosystem.team_presence(),
        "episodic_memory": ecosystem.episodic_memory(),
        "blackboard_events": ecosystem.blackboard_events("blackboard.post", {"items":h["items"]}),
        "blackboard_routing": ecosystem.blackboard_routing("blackboard", ["post","read","clear"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and h["items"]==1,"health":h,"peers":peers}

def probe(): return ecosystem.probe()

def estate_context(store_path=None):
    """Probe the real mem20 estate modules this subsystem participates in.

    The subsystem is not an isolated demo: its work is recorded in the
    delivery ledger, its scope is scored by the focus engine, its source tree
    is classified by the sitemap policy, and a memory engine is opened when a
    store path is supplied. Every value is read from a live mem20 module.
    """
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
    ledger.add("mem20visualagentblackboardz-work")
    scripts = mem20path.discover_scripts()
    focus = focus_score({"priority": 1, "distractions": 0})
    cache_skipped = is_skipped_dir("__pycache__")
    ctx = {
        "path_scripts": len(scripts),
        "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
        "work_recorded": "mem20visualagentblackboardz-work" in ledger,
        "focus_score": float(focus),
        "sitemap_skips_cache": cache_skipped,
    }
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        engine = MemoryEngine(config)
        ctx["engine_status_checked"] = engine.config is not None
    r=blackboard_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{})
    return ctx
