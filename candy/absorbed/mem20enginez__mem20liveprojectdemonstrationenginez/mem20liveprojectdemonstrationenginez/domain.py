"""Live project demonstration engine: demo flows, steps, narration."""

from __future__ import annotations

import time
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def create_demo(project, steps=None):
    return {"project": project, "steps": list(steps or []), "current": 0, "status": "ready", "started_at": None}


def add_step(demo, step):
    demo["steps"].append(step)
    return demo


def start(demo):
    demo["status"] = "running"
    demo["started_at"] = time.time()
    demo["current"] = 0
    return demo


def advance(demo):
    if demo["current"] < len(demo["steps"]) - 1:
        demo["current"] += 1
        return {"ok": True, "current": demo["current"]}
    demo["status"] = "finished"
    return {"ok": False, "reason": "end"}


def progress(demo):
    total = len(demo["steps"])
    return {"current": demo["current"], "total": total, "progress": round(demo["current"] / max(1, total), 4)}


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("demo-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "demo-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.index_health()
        ctx["engine_status_checked"] = True
    return ctx
