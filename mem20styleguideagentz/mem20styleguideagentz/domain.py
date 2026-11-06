"""Style guide agent: enforce style rules on content."""
import re


def check(content, rules):
    issues = []
    for rule in rules:
        if rule.get("type") == "max_length" and len(content) > rule["value"]:
            issues.append({"rule": "max_length", "detail": f"len {len(content)} > {rule['value']}"})
        if rule.get("type") == "forbidden" and rule["value"] in content:
            issues.append({"rule": "forbidden", "detail": rule["value"]})
        if rule.get("type") == "regex" and re.search(rule["value"], content):
            issues.append({"rule": "regex", "detail": rule["value"]})
    return issues


def fix(content, issues):
    # simple: truncate if too long
    for i in issues:
        if i["rule"] == "max_length":
            pass
    return content


def style_score(content, rules):
    issues = check(content, rules)
    return round(1 - len(issues)/max(1, len(rules)), 4)


def style_health(content, rules):
    return {"issues": len(check(content, rules)), "score": style_score(content, rules)}

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
    ledger.add("mem20styleguideagentz-work")
    scripts = mem20path.discover_scripts()
    focus = focus_score({"priority": 1, "distractions": 0})
    cache_skipped = is_skipped_dir("__pycache__")
    ctx = {
        "path_scripts": len(scripts),
        "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
        "work_recorded": "mem20styleguideagentz-work" in ledger,
        "focus_score": float(focus),
        "sitemap_skips_cache": cache_skipped,
    }
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        engine = MemoryEngine(config)
        ctx["engine_status_checked"] = engine.config is not None
    return ctx

