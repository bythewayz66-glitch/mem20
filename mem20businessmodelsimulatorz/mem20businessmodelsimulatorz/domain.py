"""Business model simulator: revenue, costs, margins, scenarios."""

from __future__ import annotations

import math
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def revenue(units, price):
    return round(units * price, 2)


def cost(fixed, variable_per_unit, units):
    return round(fixed + variable_per_unit * units, 2)


def profit(rev, cst):
    return round(rev - cst, 2)


def margin(rev, cst):
    if rev == 0:
        return 0.0
    return round((rev - cst) / rev, 4)


def break_even(fixed, price, variable_per_unit):
    contrib = price - variable_per_unit
    if contrib <= 0:
        return None
    return math.ceil(fixed / contrib)


def scenario_sim(base_units, price, fixed, var, growth=0.1, periods=4):
    out = []
    units = base_units
    for i in range(periods):
        r = revenue(units, price)
        c = cost(fixed, var, units)
        out.append(
            {
                "period": i + 1,
                "units": units,
                "revenue": r,
                "cost": c,
                "profit": profit(r, c),
                "margin": margin(r, c),
            }
        )
        units = int(units * (1 + growth))
    return out


def sensitivity(price, units, fixed, var, delta=0.1):
    base = profit(revenue(units, price), cost(fixed, var, units))
    up = profit(revenue(units, price * (1 + delta)), cost(fixed, var, units))
    down = profit(revenue(units, price * (1 - delta)), cost(fixed, var, units))
    return {"base": base, "up": up, "down": down}


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("bms-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "bms-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
