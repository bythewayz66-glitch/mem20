"""Six unique peers for Execution Digital Twin (#310), different from #300-#309."""
from __future__ import annotations
from typing import Any, Dict, Mapping, Sequence

def _safe(name, fn):
    try: return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e: return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

# 1) mem20personalworkflowtwinz
def workflow_twin(user: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20personalworkflowtwinz.domain import create_twin, efficiency_score
        twin = create_twin(dict(user or {"id": "u1", "name": "exec"}), workflows=[{"id": "w1"}])
        return {"efficiency": efficiency_score(twin)}
    return _safe("mem20personalworkflowtwinz", run)

# 2) mem20integrationdigitaltwinz
def integration_twin(system: Mapping[str, Any] = None, real_state: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20integrationdigitaltwinz.domain import create_twin, sync, drift
        twin = sync(create_twin(dict(system or {"id": "sys"})), dict(real_state or {"queue": 1}))
        return {"drift": drift(twin, dict(real_state or {"queue": 1}))}
    return _safe("mem20integrationdigitaltwinz", run)

# 3) mem20memorytimemachinez
def time_machine(state: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20memorytimemachinez.domain import checkpoint_series, diff
        snaps = checkpoint_series(dict(state or {"x": 1}), [{"x": 2}])
        return {"snapshots": len(snaps), "diff": diff(snaps[0], snaps[-1]) if len(snaps) > 1 else {}}
    return _safe("mem20memorytimemachinez", run)

# 4) mem20counterfactualmemorysimulatorz
def counterfactual_sim(memory: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20counterfactualmemorysimulatorz.domain import counterfactual, outcome_probability
        mem = dict(memory or {"state": {"x": 1}})
        return {"counterfactual": counterfactual(mem, {"action": "retry"}), "outcome_probability": outcome_probability(mem, {"type": "advance"})}
    return _safe("mem20counterfactualmemorysimulatorz", run)

# 5) mem20customerdigitaltwinlabz
def customer_twin(customer: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20customerdigitaltwinlabz.domain import build_twin, predict_churn
        twin = build_twin(dict(customer or {"id": "c1", "usage": 5}))
        return {"predict_churn": predict_churn(twin)}
    return _safe("mem20customerdigitaltwinlabz", run)

# 6) mem20crossruntimeeventlatticez
def event_lattice(events: Sequence[Mapping[str, Any]] = None) -> Dict[str, Any]:
    def run():
        from mem20crossruntimeeventlatticez.domain import emit, causal_link
        e1 = emit("twin.sync", {"id": "p1"}, source="twin")
        e2 = emit("twin.predict", {"id": "p1"}, source="twin")
        return {"causal_link": causal_link(e1 if isinstance(e1, dict) else {"id": "e1"}, e2 if isinstance(e2, dict) else {"id": "e2"})}
    return _safe("mem20crossruntimeeventlatticez", run)

def probe() -> Dict[str, Any]:
    checks = {
        "workflow_twin": workflow_twin(), "integration_twin": integration_twin(), "time_machine": time_machine(),
        "counterfactual_sim": counterfactual_sim(), "customer_twin": customer_twin(), "event_lattice": event_lattice(),
    }
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}
