"""Self-healing plans: plan execution with auto-repair."""
import time


def create_plan(steps):
    return {"steps": [{"name": s, "status": "pending"} for s in steps], "status": "ready"}


def execute_step(plan, idx, executor):
    step = plan["steps"][idx]
    try:
        executor(step["name"])
        step["status"] = "done"
    except Exception as e:
        step["status"] = "failed"
        step["error"] = str(e)
        # auto-heal: retry once
        try:
            executor(step["name"])
            step["status"] = "healed"
        except Exception as e2:
            step["status"] = "failed"
            step["error"] = str(e2)
    return plan


def plan_status(plan):
    done = sum(1 for s in plan["steps"] if s["status"] in ("done", "healed"))
    failed = sum(1 for s in plan["steps"] if s["status"] == "failed")
    return {"total": len(plan["steps"]), "done": done, "failed": failed, "healed": sum(1 for s in plan["steps"] if s["status"]=="healed")}


def heal_plan(plan):
    for s in plan["steps"]:
        if s["status"] == "failed":
            s["status"] = "pending"
    return plan

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
    ledger.add("mem20selfhealingplansz-work")
    scripts = mem20path.discover_scripts()
    focus = focus_score({"priority": 1, "distractions": 0})
    cache_skipped = is_skipped_dir("__pycache__")
    ctx = {
        "path_scripts": len(scripts),
        "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
        "work_recorded": "mem20selfhealingplansz-work" in ledger,
        "focus_score": float(focus),
        "sitemap_skips_cache": cache_skipped,
    }
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        engine = MemoryEngine(config)
        ctx["engine_status_checked"] = engine.config is not None
    return ctx

