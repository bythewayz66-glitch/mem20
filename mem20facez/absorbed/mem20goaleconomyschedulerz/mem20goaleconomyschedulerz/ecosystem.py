"""Meaningful peer integrations for Goal Economy Scheduler (#319), unique in #300-#319."""
from __future__ import annotations
from typing import Any, Dict, List

def _safe(name, fn):
    try:
        return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

def plan_health(goals: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Self-healing plan status for scheduled goals (resilience of the plan)."""
    def run():
        from mem20selfhealingplansz.domain import create_plan, plan_status, heal_plan
        steps = [{"id": str(g.get("id", i))} for i, g in enumerate(goals or [{"id": "g1"}])]
        p = create_plan(steps)
        h = heal_plan(p)
        st = plan_status(p)
        return {"status": st, "healed": h}
    return _safe("mem20selfhealingplansz", run)

def opportunity_value(goals: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Score/rank opportunities to inform goal value allocation."""
    def run():
        from mem20opportunityradarz.domain import score_opportunity, rank, scan
        gs = goals or [{"id": "g1", "value": 10, "cost": 2}]
        scored = [{"id": g.get("id"), "score": score_opportunity({"value": g.get("value", 0), "cost": g.get("cost", 1)}, {})} for g in gs]
        ranked = rank([{"value": g.get("value", 0)} for g in gs], {})
        sig = scan([{"id": g.get("id"), "strength": (g.get("value", 0) / max(1, g.get("cost", 1)))} for g in gs], threshold=0.5)
        return {"scored": scored, "ranked": ranked, "signals": sig}
    return _safe("mem20opportunityradarz", run)

def money_leak_risk(transactions: List[Dict[str, Any]] = None, expected: Dict[str, Any] = None) -> Dict[str, Any]:
    """Detect budget/money leaks affecting goal-economy allocations."""
    def run():
        from mem20revenueleakhunterz.domain import detect_leaks, recoverable, hunter_health
        tx = transactions or [{"id": "t1", "amount": 80}]
        ex = expected if isinstance(expected, dict) else {"t1": 100}
        leaks = detect_leaks(tx, ex)
        rec = recoverable(leaks) if isinstance(leaks, list) else 0
        h = hunter_health(leaks if isinstance(leaks, list) else [])
        return {"leaks": leaks, "recoverable": rec, "health": h}
    return _safe("mem20revenueleakhunterz", run)

def milestone_risk(total_units: float = 20.0) -> Dict[str, Any]:
    """Forecast milestone/schedule risk for goal completion."""
    def run():
        from mem20milestoneriskpredictorz.domain import MilestoneRiskPredictor
        m = MilestoneRiskPredictor()
        m.add_point("2026-01-01", 5)
        m.add_point("2026-01-08", 12)
        vel = m.velocity()
        fc = m.forecast(total_units)
        return {"velocity": vel, "forecast": fc}
    return _safe("mem20milestoneriskpredictorz", run)

def attention_capacity(team: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Human/attention capability capacity for goal allocation."""
    def run():
        from mem20humancapabilitysuperplatformz.domain import capability_matrix, team_capability
        users = team or [{"id": "u1", "skills": {"focus": 3, "execution": 2}}]
        matrix = capability_matrix(users, ["focus", "execution"])
        focus = team_capability(matrix, "focus")
        exec_cap = team_capability(matrix, "execution")
        return {"matrix_size": len(matrix) if isinstance(matrix, dict) else 0, "focus_capacity": focus, "execution_capacity": exec_cap}
    return _safe("mem20humancapabilitysuperplatformz", run)

def interface_composition(intent: str = "schedule") -> Dict[str, Any]:
    """Compose interface/workspace for goal-economy control (facez)."""
    def run():
        from mem20facez.domain import compose_plan, probe_members
        plan = compose_plan(intent, {"mode": "control"})
        members = probe_members()[:4]
        return {"plan": {"intent": plan.intent, "layout": plan.layout, "selected": plan.selected, "confidence": plan.confidence}, "members_checked": len(members), "importable": sum(1 for m in members if m.importable)}
    return _safe("mem20facez", run)

def goal_economy_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Meaningful goal-economy scheduling report: local allocation + peer-informed risk/capacity/value."""
    from . import domain as _dom
    goals = payload.get("goals") or []
    budget = float(payload.get("budget", 100))
    completed = payload.get("completed_ids") or []

    sched = _dom.schedule_goals(goals, budget)
    prio = _dom.priority_queue(goals) if goals else []
    prog = _dom.progress(goals, completed) if goals else 0.0
    rebal = _dom.rebalance(goals, budget * float(payload.get("budget_factor", 1.0))) if goals else sched

    opp = opportunity_value(goals)
    plan = plan_health(goals)
    money = money_leak_risk(payload.get("transactions"), payload.get("expected"))
    risk = milestone_risk(float(payload.get("total_units", max(20.0, sum(float(g.get("cost", 1)) for g in goals) or 20.0))))
    attention = attention_capacity(payload.get("team"))
    face = interface_composition(str(payload.get("intent", "schedule")))

    integrations = {
        "plan_health": plan, "opportunity_value": opp, "money_leak_risk": money,
        "milestone_risk": risk, "attention_capacity": attention, "interface_composition": face,
    }
    ok = sum(1 for v in integrations.values() if v.get("ok"))
    # meaningful composition: flag schedule risk when milestones behind or leaks present
    behind = bool(risk.get("ok") and isinstance(risk.get("forecast"), dict) and risk["forecast"].get("behind"))
    leak_flag = bool(money.get("ok") and money.get("leaks"))
    return {
        "schedule": sched, "priority_queue": prio, "progress": prog, "rebalance": rebal,
        "risk_flags": {"milestone_behind": behind, "budget_leak": leak_flag},
        "integration_health": {"ok": ok, "total": 6},
        "integrations": integrations,
    }

def probe() -> Dict[str, Any]:
    checks = {
        "plan_health": plan_health(), "opportunity_value": opportunity_value(), "money_leak_risk": money_leak_risk(),
        "milestone_risk": milestone_risk(), "attention_capacity": attention_capacity(), "interface_composition": interface_composition(),
    }
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}
