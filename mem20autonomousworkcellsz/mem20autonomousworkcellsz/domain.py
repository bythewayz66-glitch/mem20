"""Autonomous work cells: task queues, worker assignment, throughput."""

from __future__ import annotations

import time
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def create_cell(name, capacity=4):
    return {"name": name, "capacity": capacity, "queue": [], "workers": [], "completed": 0}


def enqueue(cell, task):
    cell["queue"].append(task)
    return cell


def assign_workers(cell, workers):
    cell["workers"] = workers[: cell["capacity"]]
    return cell


def process_next(cell):
    if not cell["queue"] or not cell["workers"]:
        return None
    task = cell["queue"].pop(0)
    worker = cell["workers"][cell["completed"] % len(cell["workers"])]
    cell["completed"] += 1
    return {"task": task, "worker": worker}


def throughput(cell, window_s=60):
    return round(cell["completed"] / max(1, window_s) * 60, 2)


def cell_health(cell):
    q = len(cell["queue"])
    cap = cell["capacity"]
    return {"queue_depth": q, "utilization": round(min(1.0, q / max(1, cap)), 3), "completed": cell["completed"]}


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("awc-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "awc-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
