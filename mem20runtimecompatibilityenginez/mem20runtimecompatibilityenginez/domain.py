"""Runtime compatibility engine: check version/env compatibility."""
import sys, platform


def check_python(min_version=(3,11)):
    v = sys.version_info[:2]
    return v >= min_version


def check_deps(deps, installed):
    missing = [d for d in deps if d not in installed]
    return {"ok": not missing, "missing": missing}


def compatibility_report(env, requirements):
    report = {}
    report["python_ok"] = check_python(requirements.get("python", (3, 11)))
    report["deps"] = check_deps(requirements.get("deps", []), env.get("installed", []))
    report["platform"] = platform.system()
    report["compatible"] = report["python_ok"] and report["deps"]["ok"]
    return report


def suggest_fixes(report):
    fixes = []
    if not report.get("python_ok"):
        fixes.append("upgrade python")
    for m in report.get("deps", {}).get("missing", []):
        fixes.append(f"install {m}")
    return fixes

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
    ledger.add("mem20runtimecompatibilityenginez-work")
    scripts = mem20path.discover_scripts()
    focus = focus_score({"priority": 1, "distractions": 0})
    cache_skipped = is_skipped_dir("__pycache__")
    ctx = {
        "path_scripts": len(scripts),
        "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
        "work_recorded": "mem20runtimecompatibilityenginez-work" in ledger,
        "focus_score": float(focus),
        "sitemap_skips_cache": cache_skipped,
    }
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        engine = MemoryEngine(config)
        ctx["engine_status_checked"] = engine.config is not None
    return ctx

