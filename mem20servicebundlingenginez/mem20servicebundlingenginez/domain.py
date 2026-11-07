"""Service bundling engine with 6 peers."""
from __future__ import annotations
from . import ecosystem
__all__=["create_bundle","add_service","discount","bundle_health","bundle_report","probe","estate_context"]

def create_bundle(services, name="bundle"):
    return {"name":name,"services":list(services),"price":sum(s.get("price",0) for s in services)}

def add_service(bundle, service):
    bundle["services"].append(service); bundle["price"]=sum(s.get("price",0) for s in bundle["services"]); return bundle

def discount(bundle, rate=0.1):
    bundle["price"]=round(bundle["price"]*(1-rate),2); return bundle

def bundle_health(bundles):
    return {"bundles":len(bundles),"total_price":sum(b.get("price",0) for b in bundles)}

def bundle_report():
    b=create_bundle([{"price":5},{"price":3}]); discount(b,0.1); h=bundle_health([b])
    peers={
        "deal_pricing": ecosystem.deal_pricing(b["price"]),
        "plg_sim": ecosystem.plg_sim(),
        "bundle_market": ecosystem.bundle_market("bundle", ["bundle","price","discount"]),
        "bundle_events": ecosystem.bundle_events("bundle.created", {"price":b["price"]}),
        "bundle_health_peer": ecosystem.bundle_health_peer(),
        "revenue_check": ecosystem.revenue_check(b["price"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and h["bundles"]==1,"bundle":b,"health":h,"peers":peers}

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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20servicebundlingenginez-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20servicebundlingenginez-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    else: ctx["engine_status_checked"]=False
    r=bundle_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{}); return ctx
