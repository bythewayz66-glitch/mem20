"""Offer assembly fabric: compose offers from components (6 peers)."""
from __future__ import annotations
import time
from . import ecosystem
__all__=["create_offer","add_component","price_offer","publish","offer_health","offer_report","probe","estate_context"]

def create_offer(components, price=0):
    return {"id": f"offer-{int(time.time())}", "components": list(components), "price": price, "status": "draft", "created": time.time()}

def add_component(offer, component):
    offer["components"].append(component)
    return offer

def price_offer(offer, strategy="sum"):
    if strategy == "sum":
        return sum(c.get("price", 0) for c in offer["components"])
    if strategy == "max":
        return max((c.get("price", 0) for c in offer["components"]), default=0)
    return 0

def publish(offer):
    offer["status"] = "published"
    offer["published_at"] = time.time()
    return offer

def offer_health(offers):
    published = sum(1 for o in offers if o.get("status") == "published")
    return {"total": len(offers), "published": published, "draft": len(offers)-published}

def offer_report():
    o=create_offer([{"price":5},{"price":3}],0); p=price_offer(o,"sum"); publish(o); h=offer_health([o])
    peers={
        "deal_desk": ecosystem.deal_desk(),
        "bundle_engine": ecosystem.bundle_engine(),
        "plg_sim": ecosystem.plg_sim(),
        "revenue_check": ecosystem.revenue_check(),
        "offer_events": ecosystem.offer_events("offer.published", {"price":p}),
        "offer_routing": ecosystem.offer_routing("offer", ["assemble","price","publish"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and p==8 and h["published"]==1,"price":p,"health":h,"peers":peers}

def probe(): return ecosystem.probe()

def estate_context(store_path=None):
    """Probe real mem20 estate modules; superset with peer context."""
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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20offerassemblyfabricz-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20offerassemblyfabricz-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    r=offer_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{})
    return ctx
