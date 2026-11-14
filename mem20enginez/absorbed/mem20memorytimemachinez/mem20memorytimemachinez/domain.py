"""Memory time machine: snapshot, rewind, replay, diff with mem20 integration."""

from __future__ import annotations

import copy
import json
import time
from pathlib import Path
from typing import Any

from memory_engine import EngineConfig, MemoryEngine
from memory_engine.errors import MemoryEngineError

import mem20path
from toolchest.catalog import load_inventory
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


def snapshot(state: dict[str, Any] | None = None, label: str = "", *, store_path: str | Path | None = None) -> dict[str, Any]:
    """Capture an in-memory state and, when a store is provided, engine health."""
    st = copy.deepcopy(state or {})
    health: dict[str, Any] = {}
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        engine = MemoryEngine(cfg)
        report = engine.index_health()
        health = report if isinstance(report, dict) else getattr(report, "__dict__", {"report": str(report)})
    return {"label": label, "state": st, "ts": time.time(), "engine_health": health}


def rewind(snapshots: list[dict[str, Any]], index: int) -> dict[str, Any] | None:
    if 0 <= index < len(snapshots):
        return copy.deepcopy(snapshots[index].get("state", {}))
    return None


def replay(snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [copy.deepcopy(s.get("state", {})) for s in snapshots]


def diff(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    diffs: dict[str, Any] = {}
    for k in set(a) | set(b):
        if a.get(k) != b.get(k):
            diffs[k] = {"from": a.get(k), "to": b.get(k)}
    return diffs


def timeline(snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"label": s.get("label", ""), "ts": s.get("ts")} for s in snapshots]


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    if p.exists():
        return p
    return root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict[str, Any]:
    """Gather context from sibling mem20 modules (real integration calls)."""
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("tm-probe")
    dedup_probe = "tm-probe" in ledger
    focus_probe = focus_score({"priority": 2, "distractions": 1})
    ctx: dict[str, Any] = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": bool(dedup_probe),
        "focus_probe": float(focus_probe),
    }
    if store_path is not None:
        try:
            cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
            eng = MemoryEngine(cfg)
            _ = eng.index_health()
            ctx["engine_store"] = str(cfg.store_path)
            ctx["engine_status_checked"] = True
        except MemoryEngineError as e:
            ctx["engine_error"] = str(e)
    return ctx


def checkpoint_series(initial: dict[str, Any], updates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a deterministic snapshot series from an initial state and updates."""
    snaps: list[dict[str, Any]] = []
    cur = copy.deepcopy(initial)
    snaps.append(snapshot(cur, label="initial"))
    for i, upd in enumerate(updates, 1):
        cur.update(copy.deepcopy(upd))
        snaps.append(snapshot(cur, label=f"step-{i}"))
    return snaps


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="mem20memorytimemachinez")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("--label", default="")
    s.add_argument("--state", default="{}")
    s.add_argument("--store")
    c = sub.add_parser("context")
    c.add_argument("--store")
    args = ap.parse_args(argv)
    if args.cmd == "snapshot":
        st = json.loads(args.state)
        print(json.dumps(snapshot(st, label=args.label, store_path=args.store), indent=2, sort_keys=True))
        return 0
    if args.cmd == "context":
        print(json.dumps(estate_context(args.store), indent=2, sort_keys=True))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
