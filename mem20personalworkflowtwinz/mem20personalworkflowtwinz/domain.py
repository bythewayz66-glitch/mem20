"""Personal workflow twin: mirror user workflows, suggest improvements (6 peers)."""
from __future__ import annotations
import time
from . import ecosystem
__all__=["create_twin","observe","suggest_improvements","efficiency_score","twin_health","workflow_twin_report","probe","estate_context"]


def create_twin(user, workflows=None):
    return {"user": user, "workflows": list(workflows or []), "patterns": [], "created": time.time()}


def observe(twin, event):
    twin["patterns"].append(event)
    return twin


def suggest_improvements(twin):
    suggestions = []
    # detect repeated manual steps
    from collections import Counter
    steps = [e.get("action") for e in twin["patterns"] if e.get("action")]
    for action, cnt in Counter(steps).items():
        if cnt >= 3:
            suggestions.append({"action": action, "count": cnt, "suggestion": "automate"})
    return suggestions


def efficiency_score(twin):
    if not twin["patterns"]:
        return 1.0
    manual = sum(1 for e in twin["patterns"] if e.get("manual"))
    return round(1 - manual / len(twin["patterns"]), 4)


def twin_health(twin):
    return {"workflows": len(twin["workflows"]), "patterns": len(twin["patterns"]), "efficiency": efficiency_score(twin)}


def workflow_twin_report():
    t=create_twin("u1")
    for _ in range(3): observe(t,{"action":"click"})
    sugg=suggest_improvements(t); h=twin_health(t)
    peers={
        "automation_canvas": ecosystem.automation_canvas(),
        "workcell_run": ecosystem.workcell_run(),
        "output_compile": ecosystem.output_compile(),
        "episodic_memory": ecosystem.episodic_memory(),
        "twin_events": ecosystem.twin_events("twin.suggest", {"suggestions":len(sugg)}),
        "twin_routing": ecosystem.twin_routing("twin", ["observe","suggest","efficiency"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and len(sugg)==1 and h["patterns"]==3,"suggestions":len(sugg),"health":h,"peers":peers}


def probe(): return ecosystem.probe()


def estate_context(store_path=None):
    from pathlib import Path
    import mem20path
    from memory_engine import EngineConfig, MemoryEngine
    from mem20mixedinitiativefocusenginez.domain import focus_score
    from mem20sitemapz.policy import is_skipped_dir
    from mem20webhooksupernetworkz.domain import DeliveryLedger
    from toolchest.catalog import load_inventory
    root = Path(__file__).resolve().parents[2]
    inventory_path = root / "toolchest" / "inventory.json"
    if not inventory_path.exists(): inventory_path = root / "toolchest" / "src" / "toolchest" / "inventory.json"
    inventory = load_inventory(inventory_path)
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20personalworkflowtwinz-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20personalworkflowtwinz-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    r=workflow_twin_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{})
    return ctx
