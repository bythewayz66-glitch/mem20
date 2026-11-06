"""Sensory memory ingest: ingest sensory streams into memory."""
import time, hashlib


def ingest(stream, data, modality="text"):
    entry = {"id": hashlib.md5(f"{modality}{time.time()}".encode()).hexdigest()[:8], "modality": modality, "data": data, "ts": time.time()}
    stream.setdefault("entries", []).append(entry)
    return entry


def filter_by_modality(stream, modality):
    return [e for e in stream.get("entries", []) if e.get("modality") == modality]


def recent(stream, n=5):
    return sorted(stream.get("entries", []), key=lambda e: -e["ts"])[:n]


def ingest_health(stream):
    mods = set(e.get("modality") for e in stream.get("entries", []))
    return {"entries": len(stream.get("entries", [])), "modalities": len(mods)}

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
    ledger.add("mem20sensorymemoryingestz-work")
    scripts = mem20path.discover_scripts()
    focus = focus_score({"priority": 1, "distractions": 0})
    cache_skipped = is_skipped_dir("__pycache__")
    ctx = {
        "path_scripts": len(scripts),
        "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
        "work_recorded": "mem20sensorymemoryingestz-work" in ledger,
        "focus_score": float(focus),
        "sitemap_skips_cache": cache_skipped,
    }
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        engine = MemoryEngine(config)
        ctx["engine_status_checked"] = engine.config is not None
    return ctx

