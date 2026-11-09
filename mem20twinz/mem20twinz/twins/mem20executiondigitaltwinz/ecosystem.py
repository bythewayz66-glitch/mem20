"""Six unique peers for Execution Digital Twin (#310), different from #300-#309."""
from __future__ import annotations

import concurrent.futures
from typing import Any, Callable, Dict, Mapping, Sequence

_PEER_TIMEOUT_S = 1.5
_EXEC = concurrent.futures.ThreadPoolExecutor(max_workers=6, thread_name_prefix="edt-peer")


def _safe(name: str, fn: Callable[[], Dict[str, Any]]):
    try:
        fut = _EXEC.submit(fn)
        return {"ok": True, "subsystem": name, **(fut.result(timeout=_PEER_TIMEOUT_S) or {})}
    except concurrent.futures.TimeoutError:
        fut.cancel()
        return {"ok": False, "subsystem": name, "error": f"TimeoutError: peer call timed out after {_PEER_TIMEOUT_S}s"}
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}


# 1) mem20twinz - workflow twin observation
def workflow_twin(process: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20twinz.domain import create_twin, observe, suggest_improvements, efficiency_score, twin_health
        t = create_twin(str((process or {}).get('id', 'u1')))
        observe(t, 'edit'); observe(t, 'edit'); observe(t, 'build')
        return {"improvements": suggest_improvements(t), "efficiency": efficiency_score(t), "health": twin_health(t)}
    return _safe("mem20twinz", run)


# 2) mem20twinz - integration/system twin
def integration_twin(sys: Mapping[str, Any] = None, state: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20twinz.domain import create_twin, sync, simulate, drift, health
        t = create_twin(str((sys or {}).get('id', 'sys')), dict((sys or {}).get('state') or {'q': 0}))
        sync(t, dict(state or {'q': 1, 'err': 0}))
        sim = simulate(t, [{'name': 'load', 'delta': {'q': 2}}])
        dr = drift(t, {'q': 2, 'err': 1})
        return {"simulate": sim, "drift": dr, "health": health([t])}
    return _safe("mem20twinz", run)


# 3) mem20memorytimemachinez - snapshot/replay/time travel
def time_machine(state: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20memorytimemachinez.domain import rewind, replay, diff, timeline, checkpoint_series
        snaps = [{'id': 's1', 't': 1, 'state': {'x': 1}}, {'id': 's2', 't': 2, 'state': dict(state or {'x': 2})}, {'id': 's3', 't': 3, 'state': {'x': 3}}]
        return {"rewind": rewind(snaps, 2), "diff": diff(snaps[0]['state'], snaps[1]['state']), "timeline": timeline(snaps), "checkpoints": checkpoint_series(snaps, 2), "replay": replay(snaps, 1, 3)}
    return _safe("mem20memorytimemachinez", run)


# 4) mem20simz - counterfactual outcomes
def counterfactual_sim(model: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20simz.domain import branch, counterfactual, compare, outcome_probability
        m = dict(model or {'state': {'rev': 10}, 'history': []})
        alt = branch(m, {'rev': 12})
        cf = counterfactual(m, {'rev': 15})
        return {"branch": alt, "counterfactual": cf, "compare": compare(m, cf), "outcome_probability": outcome_probability(cf, 'rev')}
    return _safe("mem20simz", run)


# 5) mem20twinz - behavior/churn/recommend
def customer_twin(customer: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20twinz.domain import build_twin, simulate_behavior, predict_churn, recommend_action
        t = build_twin(str((customer or {}).get('id', 'c1')), dict(customer or {'usage': 5}))
        return {"behavior": simulate_behavior(t, {'days': 7}), "churn": predict_churn(t), "recommend": recommend_action(t)}
    return _safe("mem20twinz", run)


# 6) mem20crossruntimeeventlatticez - causal event lattice
def event_lattice(events: Sequence[Mapping[str, Any]] = None) -> Dict[str, Any]:
    def run():
        from mem20crossruntimeeventlatticez.domain import emit, order_events, causal_link, lattice_merge, filter_by_type
        lat = {'events': [], 'nodes': {}, 'edges': []}
        for e in (events or [{'type': 'sync', 'ts': 1}, {'type': 'predict', 'ts': 2}]):
            emit(lat, dict(e))
        causal_link(lat, 'sync', 'predict')
        return {"ordered": order_events(lat.get('events', [])), "filtered": filter_by_type(lat.get('events', []), 'sync'), "merged_count": len((lattice_merge(lat, {'events': [{'type': 'audit', 'ts': 3}], 'nodes': {}, 'edges': []}) or {}).get('events', []))}
    return _safe("mem20crossruntimeeventlatticez", run)


def probe() -> Dict[str, Any]:
    checks = {
        "workflow_twin": workflow_twin(),
        "integration_twin": integration_twin(),
        "time_machine": time_machine(),
        "counterfactual_sim": counterfactual_sim(),
        "customer_twin": customer_twin(),
        "event_lattice": event_lattice(),
    }
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}
