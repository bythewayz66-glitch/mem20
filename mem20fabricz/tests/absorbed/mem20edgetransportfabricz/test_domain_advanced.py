from mem20edgetransportfabricz import domain


def test_admit_flow_prefers_feasible_low_latency_path():
    nodes = {"a": domain.FabricNode("a"), "b": domain.FabricNode("b"), "c": domain.FabricNode("c")}
    links = {
        "a->b": domain.FabricLink("a->b", "a", "b", bandwidth_mbps=100, latency_ms=5),
        "b->c": domain.FabricLink("b->c", "b", "c", bandwidth_mbps=100, latency_ms=5),
        "a->c": domain.FabricLink("a->c", "a", "c", bandwidth_mbps=10, latency_ms=50),
    }
    d = domain.admit_flow(nodes, links, domain.FlowDemand("f1", "a", "c", demand_mbps=5, priority=2, max_latency_ms=30))
    assert d.admitted and d.path == ["a", "b", "c"]
    assert d.qos in ("premium", "standard")
    sla = domain.sla_report(d, domain.FlowDemand("f1", "a", "c", demand_mbps=5, max_latency_ms=30))
    assert sla["ok"]


def test_bandwidth_constraint_and_reroute():
    nodes = {"a": domain.FabricNode("a"), "b": domain.FabricNode("b"), "c": domain.FabricNode("c")}
    links = {
        "a->b": domain.FabricLink("a->b", "a", "b", bandwidth_mbps=1, latency_ms=5),
        "b->c": domain.FabricLink("b->c", "b", "c", bandwidth_mbps=1, latency_ms=5),
        "a->c": domain.FabricLink("a->c", "a", "c", bandwidth_mbps=50, latency_ms=20),
    }
    d = domain.admit_flow(nodes, links, domain.FlowDemand("f1", "a", "c", demand_mbps=10, priority=1, max_latency_ms=100))
    assert d.admitted and d.path == ["a", "c"]
    plan = domain.reroute_plan(nodes, links, domain.FlowDemand("f1", "a", "c", demand_mbps=0.5), avoid_links=["a->c"])
    assert plan["rerouted"]


def test_intermittent_poor_connectivity_returns_degraded_plan():
    nodes = {"a": domain.FabricNode("a"), "b": domain.FabricNode("b")}
    links = {"a->b": domain.FabricLink("a->b", "a", "b", bandwidth_mbps=5, latency_ms=200, status="intermittent")}
    d = domain.admit_flow(nodes, links, domain.FlowDemand("f1", "a", "b", demand_mbps=1, priority=1, max_latency_ms=50, intermittent_ok=True))
    assert d.path == ["a", "b"]
    assert d.reasons or d.fallback_used or not d.admitted


def test_reserve_release_and_fabric_health():
    nodes = {"a": domain.FabricNode("a"), "b": domain.FabricNode("b")}
    links = {"a->b": domain.FabricLink("a->b", "a", "b", bandwidth_mbps=100, latency_ms=5)}
    res = domain.reserve_path(links, ["a->b"], 20)
    assert res["ok"] and links["a->b"].reserved_mbps == 20
    rel = domain.release_path(links, ["a->b"], 20)
    assert rel["ok"] and links["a->b"].reserved_mbps == 0
    h = domain.fabric_health(nodes, links)
    assert h["links"] == 1 and h["up_links"] == 1 and "fabric_health" in h
