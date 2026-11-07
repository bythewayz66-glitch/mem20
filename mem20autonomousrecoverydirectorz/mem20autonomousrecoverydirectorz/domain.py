"""Autonomous recovery director: incident triage, rollback, remediation."""

from __future__ import annotations

import time
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def triage(incident):
    sev = incident.get("severity", "low")
    priority = {"critical": 1, "high": 2, "medium": 3, "low": 4}.get(sev, 4)
    return {"priority": priority, "severity": sev, "auto_remediate": sev in ("low", "medium")}


def rollback_plan(state, checkpoint):
    return {
        "from_version": state.get("version"),
        "to_version": checkpoint.get("version"),
        "steps": ["stop_writes", "restore", "verify", "resume"],
    }


def remediate(incident, actions):
    applied = []
    for a in actions:
        if a.get("safe", False):
            applied.append(a)
    return {"applied": applied, "skipped": len(actions) - len(applied)}


def recovery_time(incident):
    base = {"critical": 5, "high": 15, "medium": 30, "low": 60}.get(incident.get("severity", "low"), 60)
    return base


def health_after(recovery):
    return round(min(1.0, recovery.get("success_rate", 0.5) + 0.2), 3)


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("ard-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "ard-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
