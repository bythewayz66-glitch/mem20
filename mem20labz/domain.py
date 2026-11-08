"""mem20labz domain: laboratory runtime registry, probes, runs, and aggregation.

A real control plane for the 10 member lab subsystems: discovery, health/probe
orchestration, experiment/run dispatch, and result aggregation with honest
fail-open peer reporting.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import time
import uuid
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Mapping, Optional, Sequence

from . import MEMBERS, __version__


def _now() -> float:
    return time.time()


def _run_id(prefix: str = "labrun") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def member_record(name: str) -> Dict[str, Any]:
    """Static registry record for a member lab."""
    return {
        "name": name,
        "package": name,
        "kind": "laboratory",
        "module": f"{name}.domain",
    }


def registry() -> Dict[str, Any]:
    members = [member_record(m) for m in MEMBERS]
    return {
        "runtime": "mem20labz",
        "version": __version__,
        "member_count": len(members),
        "members": members,
        "generated_at": _now(),
    }


def _import_member(name: str):
    # member layouts in this estate: <name>/<name>/domain.py
    try:
        return importlib.import_module(f"{name}.domain")
    except Exception:
        return importlib.import_module(f"{name}.{name}.domain")


def probe_member(name: str) -> Dict[str, Any]:
    """Probe a member lab via its real domain API (fail-open)."""
    started = _now()
    try:
        mod = _import_member(name)
        result: Dict[str, Any] = {"ok": True, "name": name, "domain": getattr(mod, "__name__", name)}
        # call real, safe probe/status functions when present
        if hasattr(mod, "probe") and callable(mod.probe):
            try:
                result["probe"] = mod.probe()
            except Exception as e:
                result["probe"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        for fn_name in ("healing_report", "experiment_report", "skill_report", "orchestration_report", "balance_report", "narrative_report"):
            if fn_name in result:
                continue
            if hasattr(mod, fn_name) and callable(getattr(mod, fn_name)):
                try:
                    result[fn_name] = getattr(mod, fn_name)()
                except Exception as e:
                    result[fn_name] = {"error": f"{type(e).__name__}: {e}"}
                break
        result["callables"] = sorted([n for n in dir(mod) if not n.startswith("_") and callable(getattr(mod, n, None))])[:40]
        result["elapsed_s"] = round(_now() - started, 6)
        return result
    except Exception as e:
        return {
            "ok": False,
            "name": name,
            "error": f"{type(e).__name__}: {e}",
            "elapsed_s": round(_now() - started, 6),
        }


def probe_all(members: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    targets = list(members or MEMBERS)
    results = [probe_member(m) for m in targets]
    ok = [r for r in results if r.get("ok")]
    return {
        "ok": len(ok) == len(results),
        "runtime": "mem20labz",
        "total": len(results),
        "healthy": len(ok),
        "unhealthy": len(results) - len(ok),
        "members": results,
        "probed_at": _now(),
    }


def run_member_simulation(name: str, payload: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Run a safe simulation/probe-style operation on a member lab."""
    payload = dict(payload or {})
    started = _now()
    try:
        mod = _import_member(name)
        out: Dict[str, Any] = {"ok": True, "name": name}
        # prefer explicit simulate-like functions; fall back to probe
        for fn_name, kwargs in (
            ("simulate_once", {"params": payload.get("params") or {"baseline": 1.0}, "seed": int(payload.get("seed", 0))}),
            ("simulate", {"params": payload.get("params") or {}}),
            ("monte_carlo", {"params": payload.get("params") or {"baseline": 1.0}, "n": int(payload.get("n", 10)), "seed": int(payload.get("seed", 0))}),
            ("create_experiment", {"name": payload.get("name") or f"{name}-run", "params": payload.get("params") or {}}),
            ("probe", {}),
        ):
            fn = getattr(mod, fn_name, None)
            if callable(fn):
                try:
                    # filter kwargs to signature-tolerant call
                    if fn_name == "simulate_once":
                        res = fn(kwargs["params"], seed=kwargs["seed"])
                    elif fn_name == "monte_carlo":
                        res = fn(kwargs["params"], n=kwargs["n"], seed=kwargs["seed"])
                    elif fn_name == "create_experiment":
                        res = fn(kwargs["name"], kwargs["params"])
                    elif fn_name == "simulate":
                        res = fn(payload.get("params") or {})
                    else:
                        res = fn()
                    out["operation"] = fn_name
                    out["result"] = res
                    out["elapsed_s"] = round(_now() - started, 6)
                    return out
                except TypeError:
                    try:
                        res = fn()
                        out["operation"] = fn_name
                        out["result"] = res
                        out["elapsed_s"] = round(_now() - started, 6)
                        return out
                    except Exception as e:
                        out = {"ok": False, "name": name, "operation": fn_name, "error": f"{type(e).__name__}: {e}"}
                except Exception as e:
                    return {"ok": False, "name": name, "operation": fn_name, "error": f"{type(e).__name__}: {e}", "elapsed_s": round(_now() - started, 6)}
        return {"ok": False, "name": name, "error": "No supported simulation/probe operation found", "elapsed_s": round(_now() - started, 6)}
    except Exception as e:
        return {"ok": False, "name": name, "error": f"{type(e).__name__}: {e}", "elapsed_s": round(_now() - started, 6)}


def aggregate(results: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    results = list(results or [])
    ok = sum(1 for r in results if r.get("ok"))
    errors = [ {"name": r.get("name"), "error": r.get("error")} for r in results if not r.get("ok") ]
    return {
        "total": len(results),
        "ok": ok,
        "failed": len(results) - ok,
        "success_rate": round(ok / max(1, len(results)), 4),
        "errors": errors,
    }
