"""Autonomous software foundry: spec to code, test, deploy."""

from __future__ import annotations

import hashlib
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def spec_to_tasks(spec):
    tasks = []
    for f in spec.get("features", []):
        tasks.append({"id": f"task-{f}", "feature": f, "status": "todo"})
    tasks.append({"id": "tests", "feature": "test suite", "status": "todo"})
    tasks.append({"id": "deploy", "feature": "deployment", "status": "todo"})
    return tasks


def code_quality(metrics):
    score = 0.0
    if metrics.get("tests_pass"):
        score += 0.4
    if metrics.get("coverage", 0) >= 0.8:
        score += 0.3
    if metrics.get("lint_clean"):
        score += 0.3
    return round(score, 3)


def deploy_decision(quality, threshold=0.7):
    return quality >= threshold


def estimate_effort(spec):
    base = len(spec.get("features", [])) * 2
    return {"days": base, "complexity": "high" if base > 10 else "medium" if base > 4 else "low"}


def build_artifact(spec, code):
    return {
        "name": spec.get("name"),
        "version": "0.1.0",
        "checksum": hashlib.sha256(code.encode()).hexdigest()[:12],
        "size_lines": code.count(chr(10)),
    }


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("asf-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "asf-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
