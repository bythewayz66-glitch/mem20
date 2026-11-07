"""Secure compute capsules: sandboxed execution units."""
import uuid, time


def create_capsule(code, limits=None):
    return {"id": str(uuid.uuid4())[:8], "code": code, "limits": limits or {"cpu": 1, "mem": 256}, "status": "created", "created": time.time()}


def run_capsule(capsule, runner):
    capsule["status"] = "running"
    try:
        res = runner(capsule["code"], capsule["limits"])
        capsule["result"] = res
        capsule["status"] = "completed"
    except Exception as e:
        capsule["error"] = str(e)
        capsule["status"] = "failed"
    capsule["finished"] = time.time()
    return capsule


def isolate(capsule):
    capsule["isolated"] = True
    return capsule


def capsule_health(capsules):
    return {"total": len(capsules), "completed": sum(1 for c in capsules if c.get("status")=="completed"), "failed": sum(1 for c in capsules if c.get("status")=="failed")}

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
    ledger.add("mem20securecomputecapsulesz-work")
    scripts = mem20path.discover_scripts()
    focus = focus_score({"priority": 1, "distractions": 0})
    cache_skipped = is_skipped_dir("__pycache__")
    ctx = {
        "path_scripts": len(scripts),
        "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
        "work_recorded": "mem20securecomputecapsulesz-work" in ledger,
        "focus_score": float(focus),
        "sitemap_skips_cache": cache_skipped,
    }
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        engine = MemoryEngine(config)
        ctx["engine_status_checked"] = engine.config is not None
    return ctx

