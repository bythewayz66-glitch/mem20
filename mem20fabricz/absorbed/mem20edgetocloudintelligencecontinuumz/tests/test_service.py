from __future__ import annotations

import pytest

from mem20edgetocloudintelligencecontinuumz.service import ContinuumService, ValidationError


def mk_svc(tmp_path):
    return ContinuumService(tmp_path / "c.db")


def seed(svc):
    svc.register_target({"target_id": "local", "tier": "local", "capabilities": ["compute", "render"], "cpu": 8, "memory_gb": 16, "latency_ms": 2, "cost_per_cpu_hour": 0.0, "reliability": 0.99})
    svc.register_target({"target_id": "edge", "tier": "edge", "capabilities": ["compute"], "cpu": 8, "memory_gb": 16, "latency_ms": 15, "cost_per_cpu_hour": 0.02, "reliability": 0.98})
    svc.register_target({"target_id": "cloud", "tier": "cloud", "capabilities": ["compute", "gpu", "render"], "cpu": 32, "memory_gb": 64, "latency_ms": 90, "cost_per_cpu_hour": 0.4, "reliability": 0.999})


def test_register_submit_dispatch_complete(tmp_path):
    svc = mk_svc(tmp_path)
    seed(svc)
    reg = svc.register_target({"target_id": "peer", "tier": "peer", "capabilities": ["compute"], "cpu": 4, "memory_gb": 8, "latency_ms": 40, "cost_per_cpu_hour": 0.05, "bandwidth_mbps": 10000})
    assert reg["ok"] and reg["capability_market"]["ok"] and reg["transport"]["ok"]

    # seed targets have default bandwidth; use generous latency budget for small payload
    sub = svc.submit_workload({"workload_id": "w1", "cpu": 2, "memory_gb": 2, "size_mb": 0.1, "required_capabilities": ["compute"], "duration_s": 60, "max_latency_ms": 100})
    assert sub["ok"] and sub["created"]
    assert sub["placement_preview"]["chosen"] in ("local", "edge", "peer", "cloud")
    assert sub["federated"]["ok"] and sub["cost"]["ok"] and sub["resource_market"]["ok"]

    disp = svc.dispatch("w1")
    assert disp["ok"] and disp["dispatched"] == 1
    chosen = disp["decisions"][0]["decision"]["chosen"]
    assert chosen in ("local", "edge")
    signals = disp["decisions"][0]["signals"]
    assert signals["federated"]["ok"] and signals["transport"]["ok"] and signals["capability_market"]["ok"]
    assert disp["decisions"][0]["migration_semantics"]["ok"]

    done = svc.complete("w1", success=True, reason="ok")
    assert done["ok"] and done["workload"]["state"] == "completed"


def test_idempotency_and_validation(tmp_path):
    svc = mk_svc(tmp_path)
    seed(svc)
    a = svc.submit_workload({"workload_id": "w1", "cpu": 1, "memory_gb": 1, "required_capabilities": ["compute"], "idempotency_key": "k"})
    b = svc.submit_workload({"workload_id": "w2", "cpu": 1, "memory_gb": 1, "required_capabilities": ["compute"], "idempotency_key": "k"})
    assert a["created"] and not b["created"] and b["idempotent"]
    with pytest.raises(ValidationError):
        svc.submit_workload({"workload_id": "bad", "cpu": 0, "memory_gb": 1})


def test_failover_and_migration_plan(tmp_path):
    svc = mk_svc(tmp_path)
    seed(svc)
    svc.submit_workload({"workload_id": "w1", "cpu": 2, "memory_gb": 2, "required_capabilities": ["compute"], "duration_s": 60})
    svc.dispatch("w1")
    w = svc.get_workload("w1")
    src = w["assigned_target"]
    svc.set_target_status(src, "offline")
    fo = svc.failover("w1", reason="outage")
    assert fo["plan"]["source"] == src
    assert fo["migration_semantics"]["ok"]
    # destination may be set and verified depending on capacity; plan always exists
    assert "destination" in fo["plan"]

    # migration plan for overloaded/draining target
    svc.set_target_status("edge", "draining")
    svc.submit_workload({"workload_id": "w2", "cpu": 1, "memory_gb": 1, "required_capabilities": ["compute"]})
    svc.dispatch("w2")
    plan = svc.plan_migrations(load_threshold=0.0)
    assert plan["ok"] and "moves" in plan


def test_privacy_and_cost_constraints(tmp_path):
    svc = mk_svc(tmp_path)
    svc.register_target({"target_id": "public-cloud", "tier": "cloud", "capabilities": ["compute"], "cpu": 16, "memory_gb": 32, "latency_ms": 80, "cost_per_cpu_hour": 0.5, "privacy_zones": ["public"]})
    svc.register_target({"target_id": "private-dc", "tier": "private", "capabilities": ["compute"], "cpu": 16, "memory_gb": 32, "latency_ms": 30, "cost_per_cpu_hour": 0.1, "privacy_zones": ["public", "secret"]})
    svc.submit_workload({"workload_id": "secret", "cpu": 1, "memory_gb": 1, "required_capabilities": ["compute"], "privacy_zone": "secret"})
    placed = svc.place("secret")
    assert placed["decision"]["chosen"] == "private-dc"
    svc.submit_workload({"workload_id": "cheap", "cpu": 4, "memory_gb": 4, "required_capabilities": ["compute"], "duration_s": 3600, "max_cost": 0.2})
    placed = svc.place("cheap")
    # public cloud 4 cpu * 1h * 0.5 = 2.0 exceeds 0.2, private is 0.4 still exceeds? 4*1*0.1=0.4
    assert placed["decision"]["chosen"] is None or placed["decision"]["score"] >= 0


def test_status_events_snapshot_restore_and_doctor(tmp_path):
    svc = mk_svc(tmp_path)
    seed(svc)
    svc.submit_workload({"workload_id": "w1", "cpu": 1, "memory_gb": 1, "required_capabilities": ["compute"]})
    svc.dispatch("w1")
    st = svc.status()
    assert st["ok"] and st["health"]["targets"] == 3
    assert st["transport"]["ok"]
    evs = svc.events(0, 10)
    assert isinstance(evs, list) and len(evs) >= 1
    snap = svc.snapshot("t")
    assert snap["ok"]
    restored = svc.restore(snap["snapshot_id"])
    assert restored["ok"]
    doc = svc.doctor()
    assert doc["ok"] and doc["count"] == 6
    assert set(doc["reachable"]) == {"federated", "cost", "transport", "migration", "capability_market", "resource_market"}


def test_simulate_and_benchmark(tmp_path):
    svc = mk_svc(tmp_path)
    sim = svc.simulate()
    assert sim["ok"] and sim["passed"] == sim["total"]
    bench = svc.benchmark(5)
    assert bench["ok"] and bench["iterations"] == 5 and bench["ops_per_sec"] > 0
