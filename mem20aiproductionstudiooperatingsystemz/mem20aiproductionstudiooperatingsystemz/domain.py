"""AI production studio OS: project scheduling, resource allocation, milestones."""

from __future__ import annotations

import math
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def schedule_projects(projects, capacity):
    """Schedule projects by priority within capacity."""
    sorted_p = sorted(projects, key=lambda p: (-p.get("priority", 0), p.get("deadline", float("inf"))))
    schedule = []
    used = 0
    for p in sorted_p:
        need = p.get("effort", 1)
        if used + need <= capacity:
            schedule.append({"id": p.get("id"), "start": used, "end": used + need})
            used += need
    return schedule


def resource_allocation(resources, demands):
    """Allocate resources to demands (greedy by priority)."""
    alloc = {}
    remaining = dict(resources)
    for d in sorted(demands, key=lambda x: -x.get("priority", 0)):
        rid = d.get("resource")
        need = d.get("amount", 0)
        if remaining.get(rid, 0) >= need:
            alloc[d.get("id")] = need
            remaining[rid] -= need
        else:
            alloc[d.get("id")] = 0
    return {"allocations": alloc, "remaining": remaining}


def milestone_progress(milestones, completed):
    """Compute milestone completion progress."""
    done = set(completed)
    total = len(milestones)
    finished = sum(1 for m in milestones if m.get("id") in done)
    return {"total": total, "completed": finished, "progress": round(finished / max(1, total), 4)}


def critical_path(tasks, deps):
    """Find critical path length (longest chain)."""
    memo = {}

    def longest(t):
        if t in memo:
            return memo[t]
        prereqs = deps.get(t, [])
        if not prereqs:
            memo[t] = 1
            return 1
        memo[t] = 1 + max(longest(p) for p in prereqs)
        return memo[t]

    return max((longest(t) for t in tasks), default=0)


def studio_health(projects, capacity):
    """Overall studio health score."""
    sched = schedule_projects(projects, capacity)
    utilization = sum(p.get("effort", 1) for p in projects if p.get("id") in {s["id"] for s in sched}) / max(1, capacity)
    return round(min(1.0, utilization), 4)


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("aipso-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "aipso-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
