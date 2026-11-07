"""Meaningful peer integrations for Game Production Control Center (#317), different from #300-#316.
Each adapter returns domain-useful control data (not just probes)."""
from __future__ import annotations
from typing import Any, Dict, List

def _safe(name, fn):
    try:
        return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

def team_capacity(team: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Use real-time presence to compute effective production capacity."""
    def run():
        from mem20realtimeteampresencez.domain import set_presence, online_users, away_users
        p = {}
        members = team or [{"id": "dev1", "status": "online"}, {"id": "dev2", "status": "away"}, {"id": "art1", "status": "online"}]
        for m in members:
            set_presence(p, str(m.get("id", "u")), str(m.get("status", "online")))
        online = online_users(p)
        away = away_users(p) if callable(away_users) else []
        total = len(members)
        effective = len(online) / max(1, total)
        return {"total": total, "online": online, "online_count": len(online), "away_count": len(away) if isinstance(away, list) else 0, "effective_capacity": round(effective, 4)}
    return _safe("mem20realtimeteampresencez", run)

def cost_projection(budget: Dict[str, Any] = None) -> Dict[str, Any]:
    """Use unit economics to project production cost/revenue balance."""
    def run():
        from mem20uniteconomicsautopilotz.domain import ltv, cac, payback_months, ltv_cac_ratio
        b = budget or {}
        unit_ltv = ltv(float(b.get("arpu", 10)), float(b.get("months", 12)), float(b.get("margin", 0.7)))
        unit_cac = cac(float(b.get("spend", 1000)), max(1, int(b.get("acquired", 10))))
        ratio = ltv_cac_ratio(unit_ltv, unit_cac)
        payback = payback_months(unit_cac, float(b.get("arpu", 10)) * float(b.get("margin", 0.7)))
        return {"ltv": unit_ltv, "cac": unit_cac, "ltv_cac_ratio": ratio, "payback_months": payback, "sustainable": ratio >= 3.0 if isinstance(ratio, (int, float)) else True}
    return _safe("mem20uniteconomicsautopilotz", run)

def release_readiness(services: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Use hot-swappable service foundation to assess build/release service state."""
    def run():
        from mem20hotswappableservicefoundationz.domain import register_service, swap, health, rollback
        s = {}
        for svc in (services or [{"name": "game-server", "version": "v1"}, {"name": "asset-cdn", "version": "v1"}]):
            register_service(s, str(svc.get("name", "svc")), str(svc.get("version", "v1")))
        h = health(s)
        # simulate a staged swap readiness check (no destructive swap of live state beyond model)
        swap_ok = swap(s, "game-server", "v2-candidate")
        return {"service_health": h, "candidate_swap": swap_ok, "release_ready": bool(h.get("active", 0) >= h.get("total", 0)) if isinstance(h, dict) else True}
    return _safe("mem20hotswappableservicefoundationz", run)

def capability_forge_status(payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """Use specialist model forge to assess production capability/model readiness."""
    def run():
        from mem20specialistmodelforgez.domain import forge_health
        models = (payload or {}).get("models") or [{"id": "level-design", "specialty": "design"}, {"id": "qa", "specialty": "qa"}]
        status = forge_health(models)
        return {"forge": status, "models": len(models)}
    return _safe("mem20specialistmodelforgez", run)

def resilience_assessment(project: Dict[str, Any] = None) -> Dict[str, Any]:
    """Use design stress lab to assess production resilience and recovery."""
    def run():
        from mem20executabledesignstresslabz.domain import resilience_score, recovery_time
        pr = project or {}
        checks = pr.get("checks") or [{"ok": not pr.get("scope_creep", False)}, {"ok": pr.get("budget_ratio", 1.0) <= 1.0}, {"ok": pr.get("team_size", 5) >= 3}]
        score = resilience_score(checks)
        rec = recovery_time({"redundancy": int(pr.get("redundancy", 1)), "type": "schedule-slip"})
        return {"resilience_score": score, "estimated_recovery": rec, "checks": len(checks)}
    return _safe("mem20executabledesignstresslabz", run)

def asset_animation_pipeline(assets: Dict[str, Any] = None) -> Dict[str, Any]:
    """Use rigging/animation pipeline to assess asset production readiness."""
    def run():
        from mem20rigginganimationandmotionpipelinez.domain import create_rig, set_pose, animate
        bones = list((assets or {}).get("bones") or ["root", "spine", "arm"])
        rig = create_rig(bones)
        set_pose(rig, bones[0] if bones else "root", (0, 0, 0))
        frames = (assets or {}).get("frame_data") or [{bones[0] if bones else "root": (0, 0, 0)}]
        anim = animate(rig, frames)
        return {"rig_bones": len(rig.get("bones", [])) if isinstance(rig, dict) else 0, "animation": anim}
    return _safe("mem20rigginganimationandmotionpipelinez", run)

def production_control_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Compose a meaningful production control report from local domain + 6 peer integrations."""
    from . import domain as _dom
    tasks = payload.get("tasks") or []
    capacity = int(payload.get("capacity", 10))
    milestones = payload.get("milestones") or []
    today = int(payload.get("today", 0))
    project = payload.get("project") or {}
    sprints = payload.get("sprints") or []
    completed = payload.get("completed_ids") or []

    team = team_capacity(payload.get("team"))
    effective_cap = capacity
    if team.get("ok") and isinstance(team.get("effective_capacity"), (int, float)):
        effective_cap = max(1, int(round(capacity * float(team["effective_capacity"]))))

    sprint = _dom.sprint_plan(tasks, effective_cap) if tasks else []
    burn = _dom.burndown(tasks, completed) if tasks else {"total": 0, "done": 0, "remaining": 0, "percent": 0.0}
    ms = _dom.milestone_status(milestones, today) if milestones else []
    base_risk = _dom.risk_score(project)
    resilience = resilience_assessment(project)
    # meaningful composition: adjust risk view using resilience
    if resilience.get("ok") and isinstance(resilience.get("resilience_score"), (int, float)):
        adjusted_risk = round(max(0.0, min(1.0, base_risk * (1.5 - float(resilience["resilience_score"])))), 4)
    else:
        adjusted_risk = base_risk
    health = _dom.production_health(sprints) if sprints else round(1.0 - adjusted_risk, 4)

    costs = cost_projection(payload.get("budget"))
    release = release_readiness(payload.get("services"))
    forge = capability_forge_status(payload.get("forge"))
    assets = asset_animation_pipeline(payload.get("assets"))

    integrations = {
        "team_capacity": team, "cost_projection": costs, "release_readiness": release,
        "capability_forge_status": forge, "resilience_assessment": resilience, "asset_animation_pipeline": assets,
    }
    ok_count = sum(1 for v in integrations.values() if v.get("ok"))
    return {
        "sprint_plan": sprint, "burndown": burn, "milestones": ms,
        "risk": {"base": base_risk, "adjusted": adjusted_risk},
        "production_health": health,
        "costs": costs, "release": release, "capabilities": forge, "assets": assets,
        "integration_health": {"ok": ok_count, "total": 6},
        "integrations": integrations,
    }

def probe() -> Dict[str, Any]:
    checks = {
        "team_capacity": team_capacity(), "cost_projection": cost_projection(),
        "release_readiness": release_readiness(), "capability_forge_status": capability_forge_status(),
        "resilience_assessment": resilience_assessment(), "asset_animation_pipeline": asset_animation_pipeline(),
    }
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}
