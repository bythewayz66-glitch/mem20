"""Cross-subsystem peer adapters for the edge transport fabric.

Six UNIQUE peers (different set from mem20edgefleetbrainz #300 and
mem20edgetocloudintelligencecontinuumz #301), chosen for transport/fabric
concerns. All calls are real, fail-open (errors reported, never hidden), and
exercised on covered lines.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence


def _safe(name: str, fn):
    try:
        return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}


def _link_rows(links: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    return [dict(l) for l in links]


# 1) mem20meshz.meshes.selfhealing - resilient transient delivery / retry
def mesh_resilience_probe(operation: str = "link-probe", should_fail: bool = False) -> Dict[str, Any]:
    def run():
        try:
            from mem20meshz.mem20meshz.meshes.selfhealing.domain import SelfHealingConnectorMesh
        except Exception:
            from mem20meshz.meshes.selfhealing.domain import SelfHealingConnectorMesh
        mesh = SelfHealingConnectorMesh(base_delay=0.0, factor=1.0, max_delay=0.0, jitter=False)
        attempts = {"n": 0}
        def op():
            attempts["n"] += 1
            if should_fail and attempts["n"] < 2:
                raise RuntimeError("transient")
            return {"operation": operation, "attempt": attempts["n"]}
        result = mesh.call(op, retries=2, sleep=lambda _: None)
        return {"result": result, "mesh_attempts": mesh.attempts, "delay_sample": mesh.delay_for(2)}
    return _safe("mem20meshz.meshes.selfhealing", run)


# 2) mem20autonomoustrafficcontrollerz - admission/backpressure
def traffic_admission(demand_mbps: float, rate_per_sec: float = 100.0, capacity: float = 200.0) -> Dict[str, Any]:
    def run():
        from mem20autonomoustrafficcontrollerz.domain import TokenBucket, LeakyBucket
        tb = TokenBucket(rate_per_sec=max(0.001, float(rate_per_sec)), capacity=max(0.001, float(capacity)))
        cost = max(0.0, float(demand_mbps))
        allowed = tb.allow(cost=cost, now=1.0)
        retry = tb.retry_after(cost=cost, now=1.0)
        lb = LeakyBucket(rate_per_sec=max(0.001, float(rate_per_sec)))
        lb_ok = lb.admit(now=1.0) if hasattr(lb, "admit") else None
        return {"token_bucket": {"allowed": allowed, "retry_after_s": round(float(retry), 6), "tokens_remaining": round(float(tb.tokens), 6)},
                "leaky_bucket": {"admitted": lb_ok, "type": type(lb).__name__},
                "demand_mbps": cost}
    return _safe("mem20autonomoustrafficcontrollerz", run)


# 3) mem20faultcontainmentcellsz - circuit breaker / fail-fast containment
def fault_containment(probe_ok: bool = True, threshold: int = 2) -> Dict[str, Any]:
    def run():
        from mem20faultcontainmentcellsz.domain import FaultContainmentCells, CircuitOpen
        cell = FaultContainmentCells(threshold=max(1, int(threshold)), cool_down=1.0)
        state_before = cell.state
        outcome = None
        error = None
        try:
            outcome = cell.call((lambda: {"probe": "ok"}) if probe_ok else (lambda: (_ for _ in ()).throw(RuntimeError("link down"))), now=0.0)
        except CircuitOpen as e:
            error = str(e)
        except RuntimeError as e:
            error = str(e)
        open_rejected = None
        if not probe_ok:
            try:
                cell.call(lambda: "should-not-run", now=0.0)
            except CircuitOpen as e:
                open_rejected = str(e)
            except Exception as e:
                open_rejected = f"{type(e).__name__}: {e}"
        return {"state_before": state_before, "state_after": cell.state, "outcome": outcome, "error": error, "open_rejected": open_rejected}
    return _safe("mem20faultcontainmentcellsz", run)


# 4) mem20causalroutingbrainz - causal routing influence
def causal_route(features: Mapping[str, Any], weights: Mapping[str, float], treatment: Sequence[float] = (1, 1), control: Sequence[float] = (0.5, 0.5)) -> Dict[str, Any]:
    def run():
        from mem20causalroutingbrainz.domain import route_by_cause, causal_effect, confounder_adjust, intervention_value
        score = route_by_cause(dict(features), dict(weights))
        ate = causal_effect(list(treatment), list(control))
        adjusted = confounder_adjust(float(ate), 0.1)
        ival = intervention_value(0.0, float(ate))
        return {"route_score": score, "average_treatment_effect": ate, "confounder_adjusted": adjusted, "intervention_value": ival}
    return _safe("mem20causalroutingbrainz", run)


# 5) mem20autonomousrecoverydirectorz - incident recovery planning
def recovery_plan(severity: str = "medium", component: str = "link") -> Dict[str, Any]:
    def run():
        from mem20autonomousrecoverydirectorz.domain import triage, rollback_plan, remediate, recovery_time, health_after
        incident = {"severity": severity, "component": component}
        t = triage(incident)
        rb = rollback_plan({"version": "current"}, {"version": "last-good"})
        rem = remediate(incident, [{"action": "reroute", "safe": True}, {"action": "reset", "safe": severity != "critical"}])
        eta = recovery_time(incident)
        health = health_after({"success_rate": 0.7})
        return {"triage": t, "rollback_plan": rb, "remediation": rem, "recovery_time_min": eta, "projected_health": health}
    return _safe("mem20autonomousrecoverydirectorz", run)


# 6) mem20eventstreamsuperhighwayz - fabric telemetry/flow events
def telemetry_publish(flow_id: str, event_type: str, payload: Dict[str, Any], stream_name: str = "transport-fabric") -> Dict[str, Any]:
    def run():
        from mem20eventstreamsuperhighwayz.domain import create_stream, publish, subscribe, consume, throughput, lag
        stream = create_stream(stream_name)
        subscribe(stream, "fabric-observer")
        ev = publish(stream, event_type, {"flow_id": flow_id, **(payload or {})}, key=flow_id)
        consumed = consume(stream, "fabric-observer", batch=10)
        return {"event": ev, "consumed": consumed, "throughput": throughput(stream, window_s=60), "lag": lag(stream, "fabric-observer")}
    return _safe("mem20eventstreamsuperhighwayz", run)


def probe() -> Dict[str, Any]:
    checks = {
        "mesh_selfhealing": mesh_resilience_probe(),
        "traffic_controller": traffic_admission(1.0),
        "fault_containment": fault_containment(probe_ok=True),
        "causal_routing": causal_route({"latency_ms": 20, "loss": 0.01}, {"latency_ms": -0.1, "loss": -2.0}),
        "recovery_director": recovery_plan("low"),
        "event_stream": telemetry_publish("probe", "probe", {"ok": True}),
    }
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}
