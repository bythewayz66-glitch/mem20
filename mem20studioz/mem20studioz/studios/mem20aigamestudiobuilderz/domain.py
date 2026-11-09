"""AI game studio builder: project scaffolding, asset pipeline, build config."""

from __future__ import annotations

import json
import os
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def scaffold_project(name, genre="action", engine="unity"):
    """Scaffold a game project structure."""
    return {
        "name": name,
        "genre": genre,
        "engine": engine,
        "folders": ["Assets", "Scripts", "Scenes", "Prefabs", "Audio", "UI"],
        "files": ["README.md", "project.json", ".gitignore"],
    }


def asset_pipeline(assets):
    """Plan asset import pipeline with validation."""
    pipeline = []
    for a in assets:
        pipeline.append({
            "id": a.get("id"),
            "type": a.get("type", "unknown"),
            "valid": a.get("format") in ("png", "fbx", "wav", "mp3", "json"),
            "target_dir": a.get("type", "misc") + "s",
        })
    return {"pipeline": pipeline, "valid_count": sum(1 for p in pipeline if p["valid"])}


def build_config(project, platform="pc"):
    """Generate build configuration."""
    return {
        "project": project.get("name"),
        "platform": platform,
        "output_dir": f"build/{platform}",
        "compression": "lz4" if platform == "mobile" else "none",
        "strip_debug": platform != "pc",
    }


def estimate_size(assets):
    """Estimate total build size in MB."""
    total = sum(a.get("size_mb", 0) for a in assets)
    return round(total * 1.15, 2)


def validate_project(project):
    """Validate a project has required fields."""
    required = ["name", "genre", "engine"]
    missing = [r for r in required if r not in project]
    return {"valid": not missing, "missing": missing}


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("agsb-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "agsb-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
