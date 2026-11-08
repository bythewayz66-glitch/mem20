"""mem20studioz domain: studio runtime with 6 peers."""
from __future__ import annotations
from . import ecosystem
__all__=["studio_report","probe","estate_context"]

def studio_report():
    peers={
        "audio_pipeline": ecosystem.audio_pipeline(),
        "rig_pipeline": ecosystem.rig_pipeline(),
        "production_pipeline": ecosystem.production_pipeline(),
        "studio_events": ecosystem.studio_events("studio.ready", {"ok":True}),
        "studio_routing": ecosystem.studio_routing("studio", ["audio","rig","plan"]),
        "workcell_dispatch": ecosystem.workcell_dispatch(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"peers":peers}

def probe(): return ecosystem.probe()

def estate_context(store_path: str | None = None):
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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20studioz-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20studioz-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    else: ctx["engine_status_checked"]=False
    r=studio_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{}); return ctx
