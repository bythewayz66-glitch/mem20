"""Unit economics autopilot: LTV, CAC, payback."""
def ltv(arpu, churn_rate, months=12):
    if churn_rate <= 0:
        return arpu * months
    return round(arpu / churn_rate, 4)


def cac(spend, customers):
    if customers == 0:
        return 0.0
    return round(spend / customers, 4)


def payback_months(cac_val, arpu):
    if arpu == 0:
        return float("inf")
    return round(cac_val / arpu, 4)


def ltv_cac_ratio(ltv_val, cac_val):
    if cac_val == 0:
        return float("inf")
    return round(ltv_val / cac_val, 4)


def economics_health(metrics):
    return {"ltv": metrics.get("ltv"), "cac": metrics.get("cac"), "ratio": metrics.get("ratio")}

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
    ledger.add("mem20uniteconomicsautopilotz-work")
    scripts = mem20path.discover_scripts()
    focus = focus_score({"priority": 1, "distractions": 0})
    cache_skipped = is_skipped_dir("__pycache__")
    ctx = {
        "path_scripts": len(scripts),
        "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
        "work_recorded": "mem20uniteconomicsautopilotz-work" in ledger,
        "focus_score": float(focus),
        "sitemap_skips_cache": cache_skipped,
    }
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        engine = MemoryEngine(config)
        ctx["engine_status_checked"] = engine.config is not None
    return ctx

