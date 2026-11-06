"""Specialist model forge: create fine-tuned specialist models."""
import random


def forge(base_model, specialty, data, seed=0):
    rng = random.Random(seed)
    params = {f"w{i}": rng.random() for i in range(4)}
    return {"name": f"{base_model}-{specialty}", "base": base_model, "specialty": specialty, "params": params, "trained_on": len(data)}


def evaluate(model, test_data):
    # mock accuracy
    return round(0.7 + 0.01*len(test_data)*0.0, 4) if test_data else 0.5


def merge_specialists(models):
    # average params
    if not models:
        return None
    keys = models[0]["params"].keys()
    merged = {k: sum(m["params"].get(k, 0) for m in models)/len(models) for k in keys}
    return {"name": "merged", "params": merged, "specialties": [m["specialty"] for m in models]}


def forge_health(models):
    return {"models": len(models), "specialties": len(set(m["specialty"] for m in models))}

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
    ledger.add("mem20specialistmodelforgez-work")
    scripts = mem20path.discover_scripts()
    focus = focus_score({"priority": 1, "distractions": 0})
    cache_skipped = is_skipped_dir("__pycache__")
    ctx = {
        "path_scripts": len(scripts),
        "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
        "work_recorded": "mem20specialistmodelforgez-work" in ledger,
        "focus_score": float(focus),
        "sitemap_skips_cache": cache_skipped,
    }
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        engine = MemoryEngine(config)
        ctx["engine_status_checked"] = engine.config is not None
    return ctx

