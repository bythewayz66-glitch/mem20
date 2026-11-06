"""Asset intake, cataloging, and validation pipeline."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def validate_asset(asset):
    """Validate an asset has required fields and valid format."""
    required = ["id", "type", "format"]
    missing = [r for r in required if r not in asset]
    valid_formats = {
        "image": ["png", "jpg", "webp"],
        "model": ["fbx", "gltf", "obj"],
        "audio": ["wav", "mp3", "ogg"],
    }
    fmt_ok = asset.get("format") in valid_formats.get(asset.get("type"), [])
    return {"valid": not missing and fmt_ok, "missing": missing, "format_ok": fmt_ok}


def catalog_asset(asset):
    """Create a catalog entry for an asset."""
    return {
        "id": asset.get("id"),
        "type": asset.get("type"),
        "format": asset.get("format"),
        "checksum": hashlib.sha256(str(asset).encode()).hexdigest()[:16],
        "size_bytes": asset.get("size_bytes", 0),
        "tags": asset.get("tags", []),
    }


def intake_pipeline(assets):
    """Run intake validation + cataloging pipeline."""
    results = []
    for a in assets:
        v = validate_asset(a)
        entry = catalog_asset(a) if v["valid"] else None
        results.append({
            "asset": a.get("id"),
            "valid": v["valid"],
            "catalog": entry,
            "errors": v["missing"] + ([] if v["format_ok"] else ["bad format"]),
        })
    return {"processed": len(results), "valid": sum(1 for r in results if r["valid"]), "results": results}


def search_catalog(catalog, query):
    """Search catalog by tag or type."""
    q = query.lower()
    return [
        c
        for c in catalog
        if q in str(c.get("tags", [])).lower() or q in str(c.get("type", "")).lower() or q in str(c.get("id", "")).lower()
    ]


def dedupe_assets(assets):
    """Dedupe assets by checksum."""
    seen = set()
    out = []
    for a in assets:
        cs = hashlib.sha256(str(a).encode()).hexdigest()[:16]
        if cs in seen:
            continue
        seen.add(cs)
        out.append(a)
    return out


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("aicvp-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "aicvp-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
