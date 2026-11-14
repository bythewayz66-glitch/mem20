"""Six unique peers for energy-aware foundation (#304), different from #300-#303."""
from __future__ import annotations
from typing import Any, Dict, List, Mapping, Sequence
def _safe(name, fn):
    try: return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e: return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

def resource_governance(resources: Mapping[str,float], usage: Mapping[str,float], thresholds: Mapping[str,float]=None) -> Dict[str,Any]:
    def run():
        from mem20selftuningresourcegovernorz.domain import govern, adjust_quota, governor_health
        _th = dict(thresholds or {"power_watts":0.8})
        actions = govern(dict(resources), dict(usage), _th)
        adj = {r: adjust_quota(r, resources[r], (usage.get(r,0)/max(1e-9,resources[r]))) for r in resources}
        health = governor_health(dict(resources), dict(usage))
        return {"actions": actions, "adjusted_quotas": adj, "health": health}
    return _safe("mem20selftuningresourcegovernorz", run)

def business_twin_alerts(kpis: Mapping[str,float], thresholds: Mapping[str,float]) -> Dict[str,Any]:
    def run():
        from mem20twinz.domain import create_twin, update_kpi, check_alerts, twin_health
        t = create_twin("energy-foundation")
        for k,v in (kpis or {}).items(): update_kpi(t,k,v)
        alerts = check_alerts(t, dict(thresholds or {}))
        return {"alerts": alerts, "twin_health": twin_health(t), "kpis": t.get("kpis")}
    return _safe("mem20twinz", run)

def ambient_fabric(nodes: Sequence[Mapping[str,Any]], request: Mapping[str,Any]=None) -> Dict[str,Any]:
    def run():
        from mem20freestackambientcomputingfabricz.domain import pool_resources, allocate, fabric_health
        _nodes = [dict(n) for n in (nodes or [{"cpu":4,"memory":8,"storage":10,"status":"online"}])]
        pool = pool_resources(_nodes)
        fabric = {"pool": {"cpu": pool["cpu"], "memory": pool["memory"]}, "nodes": _nodes, "total_cpu": max(1,pool["cpu"])}
        alloc = allocate(fabric, dict(request or {"cpu":1,"memory":1}))
        return {"pool": pool, "allocation": alloc, "fabric_health": fabric_health(fabric)}
    return _safe("mem20freestackambientcomputingfabricz", run)

def telemetry_aggregate(events: Sequence[Mapping[str,Any]]) -> Dict[str,Any]:
    def run():
        from mem20pipez.domain import collect_telemetry, aggregate_metrics, pipeline_report
        _events = [dict(e) for e in (events or [{"player":"device","action":"power_read"}])]
        tel = collect_telemetry(_events)
        tel["raw"] = _events
        metrics = aggregate_metrics(tel)
        report = pipeline_report([{"valid": True, **e} for e in _events])
        return {"telemetry": tel, "metrics": metrics, "report": report}
    return _safe("mem20pipez", run)

def orchestrate_actions(actions: Sequence[Mapping[str,Any]], agents: Sequence[str]=None) -> Dict[str,Any]:
    def run():
        from mem20pipez.domain import create_plan, orchestrate, pipeline_health
        tasks = [{"id": a.get("device") or f"a{i}", "priority": 1, "effort": 1, "status":"pending", **dict(a)} for i,a in enumerate(actions or [{"device":"d1","action":"reduce"}])]
        plan = create_plan([dict(t) for t in tasks], capacity=max(1,len(tasks)))
        assigns = orchestrate(plan.get("scheduled", tasks), list(agents or ["power-agent"]))
        health = pipeline_health(tasks)
        return {"plan": plan, "assignments": assigns, "pipeline_health": health}
    return _safe("mem20pipez", run)

def action_workcell(actions: Sequence[Mapping[str,Any]]) -> Dict[str,Any]:
    def run():
        from mem20autonomousworkcellsz.domain import create_cell, enqueue, assign_workers, process_next, cell_health, throughput
        c = create_cell("energy-actions", capacity=max(1, len(actions or [1])))
        for a in (actions or [{"device":"d1","action":"reduce"}]): enqueue(c, dict(a))
        assign_workers(c, ["power-worker"])
        processed = 0
        while c["queue"] and processed < 10:
            if process_next(c): processed += 1
            else: break
        return {"processed": processed, "health": cell_health(c), "throughput": throughput(c, 60)}
    return _safe("mem20autonomousworkcellsz", run)

def probe() -> Dict[str,Any]:
    checks = {
        "resource_governor": resource_governance({"power_watts":1000},{"power_watts":850}),
        "business_twin": business_twin_alerts({"watts":120},{"watts":100}),
        "ambient_fabric": ambient_fabric([{"cpu":2,"memory":4,"storage":10,"status":"online"}]),
        "telemetry": telemetry_aggregate([{"player":"meter","action":"read","watts":100}]),
        "orchestration": orchestrate_actions([{"device":"d1","action":"reduce"}]),
        "workcell": action_workcell([{"device":"d1","action":"reduce"}]),
    }
    reachable=[k for k,v in checks.items() if v.get("ok")]
    return {"ok": len(reachable)==6, "count": len(reachable), "reachable": reachable, "checks": checks}
