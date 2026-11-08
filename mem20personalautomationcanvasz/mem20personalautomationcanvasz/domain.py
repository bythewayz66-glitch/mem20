"""Personal automation canvas: workflows, triggers, actions (6 peers)."""
from __future__ import annotations
import time, uuid
from . import ecosystem
__all__=["create_canvas","add_workflow","add_trigger","run_workflow","canvas_health","canvas_report","probe","estate_context"]

def create_canvas(name, owner):
    return {"name": name, "owner": owner, "workflows": [], "triggers": []}

def add_workflow(canvas, workflow):
    canvas["workflows"].append({"id": str(uuid.uuid4())[:6], **workflow, "enabled": True})
    return canvas

def add_trigger(canvas, trigger):
    canvas["triggers"].append(trigger)
    return canvas

def run_workflow(wf, context):
    return {"workflow": wf.get("name"), "status": "completed", "steps": wf.get("steps", []), "context": context, "ran_at": time.time()}

def canvas_health(canvas):
    return {"workflows": len(canvas["workflows"]), "triggers": len(canvas["triggers"]), "enabled": sum(1 for w in canvas["workflows"] if w.get("enabled"))}

def canvas_report():
    c=create_canvas("r","u"); add_workflow(c,{"name":"w","steps":["s1"]}); h=canvas_health(c); run=run_workflow({"name":"w","steps":["s1"]},{})
    peers={
        "workcell_run": ecosystem.workcell_run(),
        "output_compile": ecosystem.output_compile(),
        "self_healing": ecosystem.self_healing(),
        "canvas_events": ecosystem.canvas_events("canvas.run", {"status":run["status"]}),
        "canvas_routing": ecosystem.canvas_routing("canvas", ["workflow","trigger","run"]),
        "causal_routing": ecosystem.causal_routing({"signal":1},{"signal":1}),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and h["workflows"]==1 and run["status"]=="completed","health":h,"run":run["status"],"peers":peers}

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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20personalautomationcanvasz-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20personalautomationcanvasz-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    r=canvas_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{})
    return ctx
