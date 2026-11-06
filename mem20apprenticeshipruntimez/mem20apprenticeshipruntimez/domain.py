"""Apprenticeship runtime: skill tracking, mentorship, progression, evaluation."""

from __future__ import annotations

import math
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def skill_level(xp):
    levels = [0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500]
    lvl = 0
    for i, t in enumerate(levels):
        if xp >= t:
            lvl = i
    return lvl


def mentor_match(apprentice, mentors):
    """Match apprentice to best mentor by skill gap."""
    best = None
    best_score = -1
    for m in mentors:
        overlap = len(set(apprentice.get("skills", [])) & set(m.get("skills", [])))
        score = overlap + m.get("experience", 0) * 0.1
        if score > best_score:
            best_score = score
            best = m
    return best


def evaluate_task(task, submission):
    """Evaluate an apprentice's task submission."""
    expected = task.get("expected", {})
    score = 0
    total = len(expected)
    for k, v in expected.items():
        if submission.get(k) == v:
            score += 1
    return {"score": score, "total": total, "pass": score >= total * 0.7}


def progression_plan(current_level, target_level):
    """Plan skill progression steps."""
    steps = []
    for lvl in range(current_level + 1, target_level + 1):
        steps.append({"level": lvl, "xp_required": lvl * 100 * (lvl + 1) // 2})
    return steps


def mentorship_hours(mentor, apprentice, weeks):
    """Compute recommended mentorship hours."""
    base = 2.0
    gap = abs(mentor.get("level", 0) - apprentice.get("level", 0))
    return round(base * (1 + gap * 0.2) * weeks, 1)


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("apr-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "apr-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
