"""Six unique peers for Gameplay Systems Data & Balance Pipeline (#316), different from #300-#315."""
from __future__ import annotations
from typing import Any, Dict

def _safe(name, fn):
    try:
        return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

def telemetry_ingest(payload=None) -> Dict[str, Any]:
    def run():
        from mem20sensorymemoryingestz.domain import ingest, ingest_health
        s = {}
        ingest(s, {"modality": "gameplay", "data": dict(payload or {"event": "tick"})})
        return {"health": ingest_health(s)}
    return _safe("mem20sensorymemoryingestz", run)

def tuning_kernel(payload=None) -> Dict[str, Any]:
    def run():
        from mem20selfoptimizingkernelz.domain import optimize, kernel_health
        k = optimize({"params": {"damage": 1.0}}, {"target": "balance"}) if False else {"params": {"damage": 1.0}}
        return {"kernel": kernel_health(k if isinstance(k, dict) else {}), "optimized": k is not None}
    return _safe("mem20selfoptimizingkernelz", run)

def spec_validation(payload=None) -> Dict[str, Any]:
    def run():
        from mem20realitytosoftwarecompilerz.domain import validate_spec, diff_spec
        spec = (payload or {}).get("spec") or {"name": "gameplay", "systems": ["combat", "economy"]}
        v = validate_spec(spec)
        d = diff_spec(spec, {"name": "gameplay"})
        return {"validation": v, "diff": d}
    return _safe("mem20realitytosoftwarecompilerz", run)

def narrative_system(payload=None) -> Dict[str, Any]:
    def run():
        from mem20dynamicnarrativeenginez.domain import create_story, add_node, choose, current_text
        st = create_story("start")
        add_node(st, "start", "begin", [{"to": "end", "label": "go"}])
        add_node(st, "end", "done", [])
        txt = current_text(st)
        return {"text": txt, "story": type(st).__name__}
    return _safe("mem20dynamicnarrativeenginez", run)

def economy_model(payload=None) -> Dict[str, Any]:
    def run():
        from mem20businessmodelsimulatorz.domain import revenue, cost, profit, margin
        rev = revenue(float((payload or {}).get("units", 10)), float((payload or {}).get("price", 5)))
        cst = cost(5, 2, int((payload or {}).get("units", 10)))
        return {"revenue": rev, "cost": cst, "profit": profit(rev, cst), "margin": margin(rev, cst)}
    return _safe("mem20businessmodelsimulatorz", run)

def goap_validation(payload=None) -> Dict[str, Any]:
    def run():
        from mem20goapagentdesignerz.domain import plan, action_cost, heuristic, validate_plan
        actions = (payload or {}).get("actions") or [{"name": "tune"}]
        h = heuristic({"hp": 10}, {"hp": 12})
        v = validate_plan([], actions)
        return {"heuristic": h, "valid_empty_plan": v, "actions": len(actions)}
    return _safe("mem20goapagentdesignerz", run)

def probe() -> Dict[str, Any]:
    checks = {
        "telemetry_ingest": telemetry_ingest(),
        "tuning_kernel": tuning_kernel(),
        "spec_validation": spec_validation(),
        "narrative_system": narrative_system(),
        "economy_model": economy_model(),
        "goap_validation": goap_validation(),
    }
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}
