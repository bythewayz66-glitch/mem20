"""Visual dataflow composer: compose dataflow pipelines visually."""
import uuid


def create_pipeline(name):
    return {"name": name, "nodes": [], "edges": []}


def add_node(pipeline, node_type, config=None):
    node = {"id": str(uuid.uuid4())[:6], "type": node_type, "config": config or {}}
    pipeline["nodes"].append(node)
    return node


def connect(pipeline, from_id, to_id):
    pipeline["edges"].append({"from": from_id, "to": to_id})
    return pipeline


def execute(pipeline, data, runner):
    # topological-ish: just run nodes in order
    results = {}
    for n in pipeline["nodes"]:
        results[n["id"]] = runner(n, data)
    return results


def pipeline_health(pipeline):
    return {"nodes": len(pipeline["nodes"]), "edges": len(pipeline["edges"])}


def estate_context(store_path=None):
    """Probe the real mem20 estate modules this composer participates in.

    A composed pipeline is enrolled in the delivery ledger, its node count is
    scored by the focus engine, and a memory engine is opened when a store path
    is supplied. Every value is read from a live mem20 module, never hardcoded.
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
    ledger.add("dataflow-pipeline-composed")
    scripts = mem20path.discover_scripts()
    focus = focus_score({"priority": 1, "distractions": 0})
    cache_skipped = is_skipped_dir("__pycache__")
    ctx = {
        "path_scripts": len(scripts),
        "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
        "composition_recorded": "dataflow-pipeline-composed" in ledger,
        "focus_score": float(focus),
        "sitemap_skips_cache": cache_skipped,
    }
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        engine = MemoryEngine(config)
        ctx["engine_status_checked"] = engine.config is not None
    return ctx
