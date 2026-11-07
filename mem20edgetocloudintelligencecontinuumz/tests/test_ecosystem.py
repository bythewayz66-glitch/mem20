from __future__ import annotations

from mem20edgetocloudintelligencecontinuumz import ecosystem


def sample_targets():
    return [
        {"target_id": "local-1", "tier": "local", "cpu": 8, "used_cpu": 1, "memory_gb": 16, "latency_ms": 2,
         "bandwidth_mbps": 500, "cost_per_cpu_hour": 0.0, "status": "online", "capabilities": ["compute"]},
        {"target_id": "cloud-1", "tier": "cloud", "cpu": 32, "used_cpu": 4, "memory_gb": 64, "latency_ms": 90,
         "bandwidth_mbps": 200, "cost_per_cpu_hour": 0.4, "status": "online", "capabilities": ["compute", "gpu"]},
    ]


def sample_workload():
    return {"workload_id": "w1", "cpu": 2, "duration_s": 120, "max_latency_ms": 150, "max_cost": 10.0,
            "priority": 50, "size_mb": 5, "required_capabilities": ["compute"]}


def test_federated_plan_returns_real_health_and_distribution():
    res = ecosystem.federated_plan(sample_targets(), sample_workload())
    assert res["ok"] and res["subsystem"] == "mem20federatedresearchgridz"
    assert "health" in res and "total" in (res["health"] or {}) and "ready" in (res["health"] or {})
    assert "distributed" in res


def test_cost_plan_computes_pipeline_and_bottleneck():
    res = ecosystem.cost_plan(sample_targets(), sample_workload())
    assert res["ok"] and res["subsystem"] == "mem20aipipelinecostoptimizerz"
    assert isinstance(res["pipeline_cost"], (int, float))
    assert "breakdown" in res and isinstance(res["breakdown"], list)


def test_transport_plan_returns_route_qos_allocation_health():
    res = ecosystem.transport_plan(sample_targets(), "local-1", "cloud-1", sample_workload())
    assert res["ok"] and res["subsystem"] == "mem20edgetransportfabricz"
    assert isinstance(res["route"], list)
    assert res["qos"] in ("premium", "standard", "best_effort")
    assert "allocation" in res and "health" in res


def test_migration_semantics_verified_and_rollback():
    ok = ecosystem.migration_semantics(sample_workload(), feasible=True)
    assert ok["ok"] and ok["subsystem"] == "mem20zerodowntimemigrationbrainz"
    assert ok["phase"] == "cutover" and ok["verified"] is True
    bad = ecosystem.migration_semantics(sample_workload(), feasible=False)
    assert bad["ok"] and bad["phase"] == "rollback" and bad["rolled_back"] is True


def test_capability_market_matches_and_reports_health():
    res = ecosystem.capability_market(sample_targets(), sample_workload())
    assert res["ok"] and res["subsystem"] == "mem20globalcapabilitymarketplacez"
    assert res["health"]["total"] >= 2
    assert "matches" in res


def test_resource_market_purchase_and_health():
    res = ecosystem.resource_market(sample_targets(), sample_workload())
    assert res["ok"] and res["subsystem"] == "mem20resourceexchangemarketz"
    assert "health" in res and res["health"]["listings"] >= 2
    assert "purchase" in res


def test_probe_reaches_all_six():
    res = ecosystem.probe()
    assert res["ok"] and res["count"] == 6
    assert len(res["reachable"]) == 6
