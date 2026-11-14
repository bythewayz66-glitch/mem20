from mem20edgetransportfabricz import ecosystem


def test_mesh_resilience_real_call():
    r = ecosystem.mesh_resilience_probe("t")
    assert r["ok"] and r["result"]["attempt"] >= 1


def test_traffic_admission_real_call():
    r = ecosystem.traffic_admission(5.0, rate_per_sec=100.0, capacity=200.0)
    assert r["ok"] and "token_bucket" in r


def test_fault_containment_real_call():
    r = ecosystem.fault_containment(probe_ok=True)
    assert r["ok"] and r["state_after"] in ("closed", "half-open", "open")


def test_causal_routing_real_call():
    r = ecosystem.causal_route({"latency_ms": 20}, {"latency_ms": -0.1})
    assert r["ok"] and "route_score" in r


def test_recovery_director_real_call():
    r = ecosystem.recovery_plan("medium")
    assert r["ok"] and r["triage"]["severity"] == "medium"


def test_event_stream_telemetry_real_call():
    r = ecosystem.telemetry_publish("f1", "probe", {"x": 1})
    assert r["ok"] and r["event"]["type"] == "probe"


def test_probe_reaches_all_six():
    p = ecosystem.probe()
    assert p["ok"] and p["count"] == 6
