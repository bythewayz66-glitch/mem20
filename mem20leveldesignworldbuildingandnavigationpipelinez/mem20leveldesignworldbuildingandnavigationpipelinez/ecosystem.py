"""6 unique peers for level/world/nav pipeline (#332). Different set from #330/#331."""
from __future__ import annotations

from typing import Any, Callable, Dict, Mapping


def _safe(name: str, fn: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
    try:
        res = fn()
        out = {"ok": True, "subsystem": name}
        if isinstance(res, dict):
            out.update(res)
        else:
            out["result"] = res
        return out
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}


def production_control_signal(level_spec: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20gameproductioncontrolcenterz.domain import sprint_plan, risk_score, milestone_status
        except Exception:
            from mem20gameproductioncontrolcenterz.mem20gameproductioncontrolcenterz.domain import sprint_plan, risk_score, milestone_status
        tasks = [{"id": f"stg-{i}", "name": s, "effort": 1} for i, s in enumerate(level_spec.get("stages") or ["blockout", "navigation"])]
        plan = sprint_plan(tasks, capacity=5)
        risk = risk_score({"tasks": tasks, "bugs": 0})
        ms = milestone_status([{"id": "m1", "due": "2099-01-01", "done": False}], today="2026-01-01")
        return {"sprint_plan": plan, "risk": risk, "milestones": ms}
    return _safe("mem20gameproductioncontrolcenterz", run)


def asset_intake_signal(level_spec: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20assetintakecatalogingandvalidationpipelinez.domain import validate_asset, catalog_asset
        except Exception:
            from mem20assetintakecatalogingandvalidationpipelinez.mem20assetintakecatalogingandvalidationpipelinez.domain import validate_asset, catalog_asset
        asset = {"id": level_spec.get("id") or "level-asset", "type": "level", "name": level_spec.get("name") or "world", "path": "levels/probe"}
        v = validate_asset(asset)
        c = catalog_asset(asset)
        return {"validation": v, "catalog": c}
    return _safe("mem20assetintakecatalogingandvalidationpipelinez", run)


def gameplay_balance_signal(level_spec: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20gameplaysystemsdataandbalancepipelinez.domain import collect_telemetry, balance_tuning
        except Exception:
            from mem20gameplaysystemsdataandbalancepipelinez.mem20gameplaysystemsdataandbalancepipelinez.domain import collect_telemetry, balance_tuning
        tel = collect_telemetry([{"event": "playability_probe", "level": level_spec.get("id", "lvl")}])
        tune = balance_tuning({"difficulty": level_spec.get("difficulty", 1.0)}, [{"metric": "completion", "value": 0.5}])
        return {"telemetry": tel, "balance_tuning": tune}
    return _safe("mem20gameplaysystemsdataandbalancepipelinez", run)


def level_architect_signal(level_spec: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20ailevelarchitectz.domain import generate_layout, pacing_profile
        except Exception:
            from mem20ailevelarchitectz.mem20ailevelarchitectz.domain import generate_layout, pacing_profile
        layout = generate_layout({"rooms": 2, "style": level_spec.get("style", "probe")})
        pacing = pacing_profile(layout if isinstance(layout, dict) else {"layout": layout})
        return {"layout": layout, "pacing": pacing}
    return _safe("mem20ailevelarchitectz", run)


def narrative_signal(level_spec: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20narrativedialogueandlocalizationpipelinez.domain import parse_dialogue, validate_dialogue
        except Exception:
            from mem20narrativedialogueandlocalizationpipelinez.mem20narrativedialogueandlocalizationpipelinez.domain import parse_dialogue, validate_dialogue
        text = level_spec.get("narrative") or "NPC: Welcome to the level.\nHERO: Ready."
        parsed = parse_dialogue(text)
        valid = validate_dialogue(parsed if parsed is not None else {"lines": []})
        return {"parsed": parsed, "validation": valid}
    return _safe("mem20narrativedialogueandlocalizationpipelinez", run)


def orchestration_signal(level_spec: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20productionplanningandtaskorchestrationpipelinez.domain import create_plan, pipeline_health
        except Exception:
            from mem20productionplanningandtaskorchestrationpipelinez.mem20productionplanningandtaskorchestrationpipelinez.domain import create_plan, pipeline_health
        tasks = [{"id": s, "effort": 1} for s in (level_spec.get("stages") or ["blockout", "navigation", "lighting"])]
        plan = create_plan(tasks, capacity=5)
        health = pipeline_health(tasks)
        return {"plan": plan, "health": health}
    return _safe("mem20productionplanningandtaskorchestrationpipelinez", run)


def pipeline_signals(level_spec: Mapping[str, Any]) -> Dict[str, Any]:
    spec = dict(level_spec or {})
    checks = {
        "production_control": production_control_signal(spec),
        "asset_intake": asset_intake_signal(spec),
        "gameplay_balance": gameplay_balance_signal(spec),
        "level_architect": level_architect_signal(spec),
        "narrative": narrative_signal(spec),
        "orchestration": orchestration_signal(spec),
    }
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}


def probe() -> Dict[str, Any]:
    return pipeline_signals({"id": "probe", "stages": ["blockout", "navigation"]})
