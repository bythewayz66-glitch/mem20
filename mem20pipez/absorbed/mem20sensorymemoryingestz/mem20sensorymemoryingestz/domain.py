"""Sensory memory ingest: ingest sensory streams into memory, with 6 peers."""
from __future__ import annotations
import time, hashlib
from . import ecosystem
__all__=["ingest","filter_by_modality","recent","ingest_health","ingest_report","probe","estate_context"]

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

def ingest_report():
    s={"entries":[]}; ingest(s,"hello","text"); ingest(s,{"px":1},"image"); h=ingest_health(s)
    peers={
        "episodic_store": ecosystem.episodic_store("sensory ingest", {"entries":h["entries"]}),
        "ingest_events": ecosystem.ingest_events("sensory.ingested", h),
        "context_compression": ecosystem.context_compression("hello sensory input"),
        "ingest_routing": ecosystem.ingest_routing("sensory", ["ingest","filter","store"]),
        "health_nervous": ecosystem.health_nervous(),
        "ingest_containment": ecosystem.ingest_containment("ingest"),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and h["entries"]==2,"health":h,"peers":peers}

def probe(): return ecosystem.probe()

def estate_context(store_path: str | None = None):
    """Probe the real mem20 estate modules plus 6 peer judgements (core API preserved)."""
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
    ctx = {
        "path_scripts": len(scripts),
        "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
        "work_recorded": "mem20sensorymemoryingestz-work" in ledger,
        "focus_score": float(focus),
        "sitemap_skips_cache": is_skipped_dir("__pycache__"),
    }
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        engine = MemoryEngine(config)
        ctx["engine_status_checked"] = engine.config is not None
    else:
        ctx["engine_status_checked"] = False
    r=ingest_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{})
    return ctx
