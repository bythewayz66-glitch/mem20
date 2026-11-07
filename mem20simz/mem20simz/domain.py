"""mem20simz domain: simulator runtime integration with 6 peers."""
from __future__ import annotations
from . import ecosystem
__all__=["sim_report","probe","estate_context"]

def sim_report():
    peers={
        "counterfactual_sim": ecosystem.counterfactual_sim({"x":1}),
        "business_twin": ecosystem.business_twin(),
        "causal_routing": ecosystem.causal_routing({"signal":1},{"signal":1}),
        "sim_events": ecosystem.sim_events("sim.run", {"ok":True}),
        "sim_routing": ecosystem.sim_routing("sim", ["simulate","forecast","compare"]),
        "sim_containment": ecosystem.sim_containment("simulate"),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"peers":peers}

def probe(): return ecosystem.probe()

def estate_context(store_path: str | None = None):
    """Probe real mem20 estate modules plus 6 peer judgements (core API preserved)."""
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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20simz-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20simz-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    else: ctx["engine_status_checked"]=False
    r=sim_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{}); return ctx
