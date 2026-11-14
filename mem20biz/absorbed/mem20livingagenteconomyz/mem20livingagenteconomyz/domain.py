"""Living agent economy: agents earn/spend, trade, reputation."""

from __future__ import annotations

from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def create_economy(agents=None):
    return {"agents": {a: {"balance": 100, "reputation": 0.5, "skills": []} for a in (agents or [])}, "transactions": []}


def earn(econ, agent, amount, reason=""):
    if agent not in econ["agents"]:
        econ["agents"][agent] = {"balance": 0, "reputation": 0.5, "skills": []}
    econ["agents"][agent]["balance"] += amount
    econ["transactions"].append({"type": "earn", "agent": agent, "amount": amount, "reason": reason})
    return econ


def spend(econ, agent, amount, reason=""):
    if econ["agents"].get(agent, {}).get("balance", 0) < amount:
        return {"ok": False, "reason": "insufficient"}
    econ["agents"][agent]["balance"] -= amount
    econ["transactions"].append({"type": "spend", "agent": agent, "amount": amount, "reason": reason})
    return {"ok": True}


def trade(econ, a, b, amount):
    if spend(econ, a, amount, "trade")["ok"]:
        earn(econ, b, amount, "trade")
        return {"ok": True}
    return {"ok": False}


def reputation(econ, agent):
    return econ["agents"].get(agent, {}).get("reputation", 0)


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("econ-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "econ-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.index_health()
        ctx["engine_status_checked"] = True
    return ctx
