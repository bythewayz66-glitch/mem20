"""Speculative workflow engine with 6 peers."""
from __future__ import annotations
from . import ecosystem
__all__=["speculate","commit","rollback","speculative_health","speculative_report","probe","estate_context"]

def speculate(workflow, branches):
    return [{"branch":b,"workflow":workflow,"status":"speculative"} for b in branches]
def commit(spec_results, chosen):
    for r in spec_results:
        if r.get("branch")==chosen: r["status"]="committed"
        elif r.get("status")=="speculative": r["status"]="discarded"
    return spec_results
def rollback(spec_results):
    for r in spec_results:
        if r.get("status")=="committed": r["status"]="rolled_back"
    return spec_results
def speculative_health(spec_results):
    return {"total":len(spec_results),"committed":sum(1 for r in spec_results if r.get("status")=="committed"),
            "rolled_back":sum(1 for r in spec_results if r.get("status")=="rolled_back")}

def speculative_report():
    r=speculate({},["b1","b2"]); commit(r,"b1"); h=speculative_health(r)
    peers={
        "counterfactual_branch": ecosystem.counterfactual_branch(),
        "causal_routing": ecosystem.causal_routing({"branches":len(r)},{"branches":1}),
        "workflow_events": ecosystem.workflow_events("workflow.committed", {"committed":h["committed"]}),
        "workflow_routing": ecosystem.workflow_routing("workflow", ["speculate","commit","rollback"]),
        "branch_containment": ecosystem.branch_containment("commit"),
        "self_healing": ecosystem.self_healing(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and h["committed"]==1,"health":h,"peers":peers}

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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20speculativeworkflowenginez-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20speculativeworkflowenginez-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    else: ctx["engine_status_checked"]=False
    r=speculative_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{}); return ctx
