"""6 unique peers for mesh orchestration (#333). Different set from #330/#331/#332."""
from __future__ import annotations
from typing import Any, Callable, Dict


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


def eventstream_signal(mesh: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20eventstreamsuperhighwayz.domain import create_stream, publish, throughput
        except Exception:
            from mem20eventstreamsuperhighwayz.mem20eventstreamsuperhighwayz.domain import create_stream, publish, throughput
        s = create_stream("meshz-probe")
        publish(s, "mesh.execute", {"mesh": mesh.get("mesh", "mem20meshz")}, key="probe")
        t = throughput(s, window_s=60)
        return {"stream": (s.get("name") if isinstance(s, dict) else "meshz-probe"), "throughput": t}
    return _safe("mem20eventstreamsuperhighwayz", run)


def execution_twin_signal(mesh: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20executiondigitaltwinz.domain import create_twin, simulate, predict_outcome
        except Exception:
            from mem20executiondigitaltwinz.mem20executiondigitaltwinz.domain import create_twin, simulate, predict_outcome
        twin = create_twin({"id": "meshz-twin", "workload": mesh.get("mesh", "mem20meshz")})
        sim = simulate(twin, [{"event": "probe"}])
        pred = predict_outcome(twin, {"action": "probe"})
        return {"twin_id": (twin.get("id") if isinstance(twin, dict) else None), "simulated": sim is not None, "prediction": pred}
    return _safe("mem20executiondigitaltwinz", run)


def federated_grid_signal(mesh: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20federatedresearchgridz.domain import register_node, aggregate_results, grid_health
        except Exception:
            from mem20federatedresearchgridz.mem20federatedresearchgridz.domain import register_node, aggregate_results, grid_health
        grid = {"nodes": [], "tasks": []}
        n = register_node(grid, {"id": "meshz-node", "kind": "mesh"})
        agg = aggregate_results([])
        h = grid_health(grid)
        return {"node_id": "meshz-node", "registered": n is not None, "aggregate": agg, "health": h}
    return _safe("mem20federatedresearchgridz", run)


def recovery_signal(mesh: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20autonomousrecoverydirectorz.domain import triage, recovery_report, health_after
        except Exception:
            from mem20autonomousrecoverydirectorz.mem20autonomousrecoverydirectorz.domain import triage, recovery_report, health_after
        tri = triage({"service": "meshz", "error": "probe", "severity": "low"})
        rep = recovery_report([tri])
        ha = health_after({"remediation": [{"applied": "restart"}]})
        return {"triage": tri, "report": rep, "health_after": ha}
    return _safe("mem20autonomousrecoverydirectorz", run)


def counterfactual_signal(mesh: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20counterfactualmemorysimulatorz.domain import counterfactual, compare, outcome_probability
        except Exception:
            from mem20counterfactualmemorysimulatorz.mem20counterfactualmemorysimulatorz.domain import counterfactual, compare, outcome_probability
        cf = counterfactual({"s": 1}, {"s": 2})
        cmp = compare({"a": 1}, {"a": 2})
        prob = outcome_probability({"base_rate": 0.5}, {"effect": 0.1})
        return {"counterfactual": cf, "compare": cmp, "probability": prob}
    return _safe("mem20counterfactualmemorysimulatorz", run)


def protocol_discovery_signal(mesh: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        try:
            from mem20protocolautodiscoveryenginez.domain import detect_protocol, register_protocol, protocol_health
        except Exception:
            from mem20protocolautodiscoveryenginez.mem20protocolautodiscoveryenginez.domain import detect_protocol, register_protocol, protocol_health
        detected = detect_protocol(b"GET / HTTP/1.1\r\nHost: mesh\r\n\r\n")
        registry = {}
        register_protocol(registry, "http", {"handler": "meshz"})
        health = protocol_health(registry)
        return {"detected": detected, "registry_size": len(registry), "health": health}
    return _safe("mem20protocolautodiscoveryenginez", run)


def mesh_signals(mesh: Dict[str, Any] | None = None) -> Dict[str, Any]:
    ctx = dict(mesh or {"mesh": "mem20meshz"})
    checks = {
        "eventstream": eventstream_signal(ctx),
        "execution_twin": execution_twin_signal(ctx),
        "federated_grid": federated_grid_signal(ctx),
        "recovery": recovery_signal(ctx),
        "counterfactual": counterfactual_signal(ctx),
        "protocol_discovery": protocol_discovery_signal(ctx),
    }
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}


def probe() -> Dict[str, Any]:
    return mesh_signals()
