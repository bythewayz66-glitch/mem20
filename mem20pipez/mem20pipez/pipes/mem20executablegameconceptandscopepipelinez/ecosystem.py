"""Six unique peers for Executable Game Concept & Scope Pipeline (#309), different from #300-#308."""
from __future__ import annotations
from typing import Any, Dict, Mapping

def _safe(name, fn):
    try: return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e: return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

# 1) mem20gameproductioncontrolcenterz - sprint/milestone/risk planning
def production_control(concept: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20gameproductioncontrolcenterz.domain import sprint_plan, milestone_status, risk_score
        tasks = [{"id": "t1", "points": 3}, {"id": "t2", "points": 5}]
        plan = sprint_plan(tasks, capacity=8)
        ms = milestone_status([{"id": "m1", "due_day": 30, "tasks": ["t1", "t2"]}], 10)
        risk = risk_score(dict(concept or {"complexity": "medium", "team_size": 5, "scope_creep": False, "budget_ratio": 1.0}))
        return {"sprint_plan": plan, "milestone_status": ms, "risk_score": risk}
    return _safe("mem20gameproductioncontrolcenterz", run)

# 2) mem20aiproductionstudiooperatingsystemz - scheduling/resource/milestones
def studio_ops(concept: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20aiproductionstudiooperatingsystemz.domain import schedule_projects, resource_allocation, studio_health
        projects = [{"id": "p1", "effort": 10, "priority": 1}]
        sched = schedule_projects(projects, capacity=20)
        alloc = resource_allocation({"eng": 10, "art": 5}, [{"id": "d1", "resource": "eng", "amount": 5, "priority": 1}])
        health = studio_health(projects, 20)
        return {"schedule": sched, "allocation": alloc, "studio_health": health}
    return _safe("mem20aiproductionstudiooperatingsystemz", run)

# 3) mem20simz - product/growth feasibility
def growth_feasibility(concept: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20simz.domain import viral_coefficient, retention_curve, growth_score
        v = viral_coefficient(2.0, 0.15)
        ret = retention_curve(1000, 0.1, periods=6)
        gs = growth_score({"viral_k": v if isinstance(v, (int, float)) else 0.3, "conversion": 0.2, "retention": 0.7})
        return {"viral_coefficient": v, "retention_curve": ret, "growth_score": gs}
    return _safe("mem20simz", run)

# 4) mem20autonomoussoftwarefoundryz - spec-to-tasks/effort/build
def software_foundry(concept: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20autonomoussoftwarefoundryz.domain import spec_to_tasks, estimate_effort, deploy_decision
        spec = dict(concept or {"name": "game", "features": ["core", "ui", "save"]})
        tasks = spec_to_tasks(spec)
        est = estimate_effort(spec)
        dep = deploy_decision(0.85, threshold=0.7)
        return {"tasks": tasks, "estimate_effort": est, "deploy_decision": dep}
    return _safe("mem20autonomoussoftwarefoundryz", run)

# 5) mem20aigamestudiobuilderz - game project scaffold/validation
def game_studio(concept: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20aigamestudiobuilderz.domain import scaffold_project, build_config, validate_project
        c = dict(concept or {"name": "concept", "genre": "action", "features": ["f1"]})
        proj = scaffold_project(c.get("name", "concept"), genre=c.get("genre", "action"), engine=c.get("engine", "unity"))
        cfg = build_config(proj if isinstance(proj, dict) else {"name": c.get("name", "concept")}, platform="pc")
        val = validate_project(proj if isinstance(proj, dict) else {"name": c.get("name", "concept"), "genre": "action"})
        return {"project": proj, "build_config": cfg, "validate": val}
    return _safe("mem20aigamestudiobuilderz", run)

# 6) mem20autonomousmicrosaasfoundryz - idea scoring/MVP/revenue
def microsaas_foundry(concept: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20autonomousmicrosaasfoundryz.domain import score_idea, mvp_spec, revenue_projection
        idea = dict(concept or {"name": "game-tool", "market_size": 700, "competition": 4, "effort": 3})
        score = score_idea(idea)
        mvp = mvp_spec(idea)
        rev = revenue_projection(100, 10.0, churn=0.05)
        return {"score": score, "mvp": mvp, "revenue_projection": rev}
    return _safe("mem20autonomousmicrosaasfoundryz", run)

def probe() -> Dict[str, Any]:
    checks = {"production_control": production_control(), "studio_ops": studio_ops(), "growth_feasibility": growth_feasibility(),
              "software_foundry": software_foundry(), "game_studio": game_studio(), "microsaas_foundry": microsaas_foundry()}
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}
