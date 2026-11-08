"""Specialist model forge with 6 peers."""
from __future__ import annotations
import random
from . import ecosystem
__all__=["forge","evaluate","merge_specialists","forge_health","forge_report","probe","estate_context"]

def forge(base_model, specialty, data, seed=0):
    rng=random.Random(seed); return {"name":f"{base_model}-{specialty}","specialty":specialty,"data_n":len(data),"score":round(rng.random(),4)}

def evaluate(model, test_data):
    base=model.get("score",0.5); return round(min(1.0,max(0.0, base + 0.01*len(test_data))),4)

def merge_specialists(models):
    if not models: return {"name":"merged-empty","specialties":[]}
    return {"name":"merged-"+ "-".join(m.get("specialty","x") for m in models[:2]),"specialties":[m.get("specialty") for m in models]}

def forge_health(models):
    return {"models":len(models),"avg_score": round(sum(m.get("score",0) for m in models)/len(models),4) if models else 0}

def forge_report():
    m=forge("base","code",["d1"],seed=1); ev=evaluate(m,["t1"]); h=forge_health([m])
    peers={
        "collective_intel": ecosystem.collective_intel(),
        "causal_routing": ecosystem.causal_routing({"score":m.get("score",0)},{"score":1}),
        "forge_events": ecosystem.forge_events("model.forged", {"specialty":m["specialty"],"eval":ev}),
        "forge_routing": ecosystem.forge_routing("forge", ["train","eval","merge"]),
        "forge_containment": ecosystem.forge_containment("forge"),
        "software_foundry": ecosystem.software_foundry(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and h["models"]==1,"model":m,"eval":ev,"health":h,"peers":peers}

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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20specialistmodelforgez-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20specialistmodelforgez-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    else: ctx["engine_status_checked"]=False
    r=forge_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{}); return ctx
