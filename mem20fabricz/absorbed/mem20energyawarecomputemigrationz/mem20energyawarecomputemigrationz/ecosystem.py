"""Cross-subsystem peer adapters for energy-aware compute migration.

Six UNIQUE peers (different set from #300, #301, #302), chosen for
energy/carbon/battery, locality, capacity forecasting, goal scheduling, and
batch fabric placement. Real calls, fail-open reporting.
"""

from __future__ import annotations
from typing import Any, Dict, List, Mapping, Sequence

def _safe(name, fn):
    try: return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e: return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

# 1) mem20batteryawareagentschedulerz - power budget / battery feasibility
def battery_schedule(work_units: float, hours: Sequence[int], power_budget_watts: float = 500.0, rates: Mapping[int, float] = None) -> Dict[str, Any]:
    def run():
        from mem20batteryawareagentschedulerz.domain import BatteryAwareAgentScheduler
        _rates = dict(rates or {h: 50.0 + (h % 6) * 10.0 for h in (hours or [0,1,2,3])})
        sched = BatteryAwareAgentScheduler(power_budget_watts=max(1.0, float(power_budget_watts)), rates=_rates)
        result = sched.schedule(float(work_units), list(hours or rates.keys()))
        return {"schedule": result, "deferred": sched.deferred}
    return _safe("mem20batteryawareagentschedulerz", run)

# 2) mem20energyawarefoundationz - energy budget/threshold/power optimization
def energy_foundation(devices: Sequence[Mapping[str, Any]], budget_watts: float = 1000.0, threshold_watts: float = 800.0) -> Dict[str, Any]:
    def run():
        from mem20energyawarefoundationz.domain import power_reading, threshold_check, energy_budget, optimize_power, daily_energy
        devs = [dict(d) for d in (devices or [])]
        readings = [power_reading(d) for d in devs] if devs else [{"device": "probe", "watts": 100, "timestamp": 0}]
        checks = [threshold_check(r, float(threshold_watts)) for r in readings]
        budget = energy_budget(devs or [{"id":"probe","power_watts":100}], float(budget_watts))
        actions = optimize_power(devs or [{"id":"probe","power_watts":100}], target_reduction=0.1)
        daily = daily_energy(devs or [{"id":"probe","power_watts":100}], hours=24)
        return {"readings": readings, "threshold_checks": checks, "budget": budget, "optimize_actions": actions, "daily_kwh": daily}
    return _safe("mem20energyawarefoundationz", run)

# 3) mem20datalocalityoptimizerz - migration/locality cost
def data_locality(data: Mapping[str, Any], nodes: Sequence[Mapping[str, Any]], src: Mapping[str, Any] = None, dst: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20datalocalityoptimizerz.domain import placement_score, optimal_placement, migration_cost, locality_report
        _data = dict(data or {"id":"d","size_gb":1})
        _nodes = [dict(n) for n in (nodes or [])]
        best = optimal_placement(_data, [dict(n) for n in _nodes]) if _nodes else None
        score = placement_score(_nodes[0], _data) if _nodes else None
        mcost = migration_cost(_data, dict(src or {"egress_cost":0.09}), dict(dst or {"egress_cost":0.0})) if src or dst else migration_cost(_data, {"egress_cost":0.09}, {"egress_cost":0.0})
        report = locality_report([{"local": best and best.get("id")==_data.get("node")}])
        return {"best_node": best, "placement_score": score, "migration_cost": mcost, "locality_report": report}
    return _safe("mem20datalocalityoptimizerz", run)

# 4) mem20causalroutingbrainz - capacity forecast for targets
def capacity_forecast(observations: Sequence[float], steps: int = 1) -> Dict[str, Any]:
    def run():
        from mem20causalroutingbrainz.domain import DemandForecastAndCapacityBrain
        brain = DemandForecastAndCapacityBrain(alpha=0.3, window=50)
        for v in (observations or [1.0, 1.1, 0.9, 1.2]):
            brain.observe(float(v))
        fc = brain.forecast(steps=max(1, int(steps)))
        sigma = brain.residual_sigma()
        cap = None
        if hasattr(brain, "capacity_for"):
            try: cap = brain.capacity_for(0.99)
            except Exception as e: cap = {"error": str(e)}
        return {"forecast": fc, "residual_sigma": sigma, "capacity": cap, "n": len(brain.observations)}
    return _safe("mem20causalroutingbrainz", run)

# 5) mem20goaleconomyschedulerz - prioritize migrations by value/cost
def goal_priority(goals: Sequence[Mapping[str, Any]], budget: float = 10.0) -> Dict[str, Any]:
    def run():
        from mem20goaleconomyschedulerz.domain import schedule_goals, goal_value, priority_queue, progress
        _goals = [dict(g) for g in (goals or [{"id":"m1","value":5,"cost":1},{"id":"m2","value":3,"cost":2}])]
        sched = schedule_goals(_goals, float(budget))
        queue = priority_queue(_goals)
        vals = {g.get("id"): goal_value(g) for g in _goals}
        prog = progress(_goals, sched.get("scheduled", []))
        return {"schedule": sched, "priority_queue": [g.get("id") for g in queue], "values": vals, "progress": prog}
    return _safe("mem20goaleconomyschedulerz", run)

# 6) mem20planetarybatchfabricz - batch workload placement/fabric health
def batch_fabric(jobs: Sequence[Mapping[str, Any]] = None, regions: Mapping[str, int] = None) -> Dict[str, Any]:
    def run():
        from mem20planetarybatchfabricz.domain import submit_job, schedule, fabric_health, retry
        _regions = dict(regions or {"local": 2, "edge": 2})
        _jobs = [dict(j) for j in (jobs or [{"id":"j1","region":"local","priority":1,"status":"queued"},{"id":"j2","region":"edge","priority":2,"status":"queued"}])]
        scheduled = schedule(_jobs, dict(_regions))
        health = fabric_health(_regions)
        sample = submit_job("local", {"kind":"migration"}, priority=1)
        rt = retry(dict(sample, status="failed", retries=0))
        return {"scheduled": [{"id":j.get("id"),"status":j.get("status"),"region":j.get("region")} for j in scheduled],
                "fabric_health": health, "retry_probe": rt, "submitted_sample": sample.get("status")}
    return _safe("mem20planetarybatchfabricz", run)

def probe() -> Dict[str, Any]:
    checks = {
        "battery_scheduler": battery_schedule(10, [0,1,2], 500, {0:50,1:60,2:40}),
        "energy_foundation": energy_foundation([{"id":"n1","power_watts":120}], 500, 200),
        "data_locality": data_locality({"id":"d1","size_gb":1,"node":"n1"}, [{"id":"n1","capacity_gb":10,"used_gb":0,"latency_ms":5,"cost_per_gb":0.01}]),
        "capacity_forecast": capacity_forecast([10,11,9,12,10,11]),
        "goal_scheduler": goal_priority([{"id":"m1","value":5,"cost":1}], 5),
        "batch_fabric": batch_fabric(),
    }
    reachable = [k for k,v in checks.items() if v.get("ok")]
    return {"ok": len(reachable)==6, "count": len(reachable), "reachable": reachable, "checks": checks}
