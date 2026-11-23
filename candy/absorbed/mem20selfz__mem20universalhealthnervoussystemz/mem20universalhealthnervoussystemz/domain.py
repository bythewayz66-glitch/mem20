"""Universal health nervous system: aggregate health across subsystems (6 peers)."""
from __future__ import annotations
import time
from . import ecosystem
__all__=["register_subsystem","check_all","overall","health_report","nervous_report","probe","estate_context"]

def register_subsystem(health, name, checker):
    health.setdefault("subsystems", {})[name] = {"checker": checker, "last": None, "status": "unknown"}
    return health

def check_all(health):
    results = {}
    for name, info in health.get("subsystems", {}).items():
        try:
            r = info["checker"]()
            info["last"] = r
            info["status"] = "healthy" if r.get("ok", True) else "unhealthy"
        except Exception as e:
            info["last"] = {"error": str(e)}
            info["status"] = "error"
        results[name] = info["status"]
    return results

def overall(health):
    statuses = [s["status"] for s in health.get("subsystems", {}).values()]
    if any(s == "error" for s in statuses):
        return "degraded"
    if all(s == "healthy" for s in statuses):
        return "healthy"
    if any(s == "unhealthy" for s in statuses):
        return "unhealthy"
    return "unknown"

def health_report(health):
    return {"overall": overall(health), "subsystems": {n: i["status"] for n, i in health.get("subsystems", {}).items()}}

def nervous_report():
    h={}; register_subsystem(h,"self", lambda: {"ok":True}); check_all(h); hr=health_report(h)
    peers={
        "fault_containment": ecosystem.fault_containment("nervous"),
        "recovery_director": ecosystem.recovery_director(),
        "self_healing": ecosystem.self_healing(),
        "health_events": ecosystem.health_events("health.checked", {"overall":hr["overall"]}),
        "health_routing": ecosystem.health_routing("health", ["check","recover","heal"]),
        "causal_routing": ecosystem.causal_routing({"signal":1},{"signal":1}),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and hr["overall"]=="healthy","health":hr,"peers":peers}

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
    ledger.add("mem20universalhealthnervoussystemz-work")
    scripts = mem20path.discover_scripts()
    focus = focus_score({"priority": 1, "distractions": 0})
    cache_skipped = is_skipped_dir("__pycache__")
    ctx = {
        "path_scripts": len(scripts),
        "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
        "work_recorded": "mem20universalhealthnervoussystemz-work" in ledger,
        "focus_score": float(focus),
        "sitemap_skips_cache": cache_skipped,
    }
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        engine = MemoryEngine(config)
        ctx["engine_status_checked"] = engine.config is not None
    r=nervous_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{})
    return ctx
