"""Six unique peers for Intent-to-Mission Compiler (#330)."""
from __future__ import annotations

import concurrent.futures
from typing import Any, Callable, Dict, Mapping

_PEER_TIMEOUT_S = 2.0
_EXEC = concurrent.futures.ThreadPoolExecutor(max_workers=6, thread_name_prefix="itmc-peer")


def _safe(name: str, fn: Callable[[], Dict[str, Any]]):
    try:
        fut = _EXEC.submit(fn)
        return {"ok": True, "subsystem": name, **(fut.result(timeout=_PEER_TIMEOUT_S) or {})}
    except concurrent.futures.TimeoutError:
        fut.cancel()
        return {"ok": False, "subsystem": name, "error": f"TimeoutError: peer call timed out after {_PEER_TIMEOUT_S}s"}
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}


def intent_parse(goal: str) -> Dict[str, Any]:
    def run():
        from mem20intentcompilerz.domain import parse_intent, classify, compile_to_action, validate, intent_confidence
        intent = parse_intent(goal or "execute mission")
        cls = classify(intent)
        action = compile_to_action(intent)
        valid = validate(intent)
        conf = intent_confidence(intent, [w for w in str(goal).lower().split() if len(w) > 2][:5])
        return {"intent": intent, "class": cls, "action": action, "valid": valid, "confidence": conf}
    return _safe("mem20intentcompilerz", run)


def goal_schedule(mission: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20goaleconomyschedulerz.domain import schedule_goals, priority_queue, progress
        goals = [{"id": s.get("id"), "value": max(1, len(s.get("action", ""))), "cost": 1, "status": s.get("status", "pending")} for s in (mission.get("steps") or [])]
        sched = schedule_goals(goals, budget=max(1, len(goals)))
        pq = priority_queue(goals)
        prog = progress(goals, [g["id"] for g in goals if g.get("status") == "done"])
        return {"schedule": sched, "priority_queue": pq, "progress": prog}
    return _safe("mem20goaleconomyschedulerz", run)


def priority_collisions(mission: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20prioritycollisionresolverz.domain import PriorityCollisionResolver
        r = PriorityCollisionResolver()
        for i, s in enumerate(mission.get("steps") or []):
            item = {"id": s.get("id"), "action": s.get("action")}
            if hasattr(r, "submit"):
                r.submit(item, len(mission.get("steps") or []) - i)
            elif hasattr(r, "add"):
                r.add(item, priority=len(mission.get("steps") or []) - i)
        resolved = r.resolve() if hasattr(r, "resolve") else {"resolver": type(r).__name__}
        return {"resolved": resolved}
    return _safe("mem20prioritycollisionresolverz", run)


def skill_roles(mission: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20dynamicskillgraphz.domain import add_skill, update_proficiency, skill_gap, learning_path, graph_stats
        g = {"skills": {}, "edges": []}
        for s in (mission.get("steps") or []):
            role = str(s.get("role") or "executor")
            add_skill(g, role, prereqs=[])
            update_proficiency(g, role, 0.2)
            action = str(s.get("action") or "task")[:24]
            add_skill(g, action, prereqs=[role])
        required = [str(s.get("role") or "executor") for s in (mission.get("steps") or [])]
        gap = skill_gap(g, list(dict.fromkeys(required)))
        path = learning_path(g, required[0]) if required else []
        return {"skill_gap": gap, "learning_path": path, "stats": graph_stats(g)}
    return _safe("mem20dynamicskillgraphz", run)


def reversible_plan(mission: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20reversibleexecutiongraphz.domain import create_graph, add_node, undo, redo, graph_health
        g = create_graph()
        for s in (mission.get("steps") or []):
            add_node(g, {"id": s.get("id"), "op": s.get("action"), "depends_on": s.get("depends_on")})
        u = undo(g)
        r = redo(g)
        return {"undo": u, "redo": r, "health": graph_health(g)}
    return _safe("mem20reversibleexecutiongraphz", run)


def self_heal_plan(mission: Mapping[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20selfhealingplansz.domain import create_plan, plan_status, heal_plan
        plan = create_plan([{"id": s.get("id"), "op": s.get("action"), "depends_on": s.get("depends_on", [])} for s in (mission.get("steps") or [])])
        status = plan_status(plan)
        healed = heal_plan(plan)
        return {"status": status, "healed": healed, "step_count": len(plan.get("steps") or [])}
    return _safe("mem20selfhealingplansz", run)


def compile_signals(goal: str, mission: Mapping[str, Any]) -> Dict[str, Any]:
    checks = {
        "intent_parse": intent_parse(goal),
        "goal_schedule": goal_schedule(mission),
        "priority_collisions": priority_collisions(mission),
        "skill_roles": skill_roles(mission),
        "reversible_plan": reversible_plan(mission),
        "self_heal_plan": self_heal_plan(mission),
    }
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}


def probe() -> Dict[str, Any]:
    sample = {"mission_id": "probe", "steps": [{"id": "s1", "action": "plan", "role": "planner", "status": "pending", "depends_on": [], "completion_criteria": ["done"]}]}
    return compile_signals("plan mission", sample)
