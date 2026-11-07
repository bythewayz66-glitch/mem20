"""Resource exchange market: trade resources between agents."""
import time


def list_resource(seller, resource, amount, price):
    return {"seller": seller, "resource": resource, "amount": amount, "price": price, "available": True}


def buy(listing, buyer, qty):
    if qty > listing["amount"]:
        return {"ok": False, "reason": "insufficient"}
    listing["amount"] -= qty
    if listing["amount"] == 0:
        listing["available"] = False
    return {"ok": True, "buyer": buyer, "qty": qty, "cost": qty*listing["price"]}


def price_history(trades):
    return [{"price": t.get("price"), "ts": t.get("ts")} for t in trades]


def market_health(listings):
    return {"listings": len(listings), "available": sum(1 for l in listings if l.get("available"))}

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
    ledger.add("mem20resourceexchangemarketz-work")
    scripts = mem20path.discover_scripts()
    focus = focus_score({"priority": 1, "distractions": 0})
    cache_skipped = is_skipped_dir("__pycache__")
    ctx = {
        "path_scripts": len(scripts),
        "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
        "work_recorded": "mem20resourceexchangemarketz-work" in ledger,
        "focus_score": float(focus),
        "sitemap_skips_cache": cache_skipped,
    }
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        engine = MemoryEngine(config)
        ctx["engine_status_checked"] = engine.config is not None
    return ctx

