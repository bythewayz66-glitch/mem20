"""Service tests: the full submit -> place -> run -> finish lifecycle.

Each test drives the same methods the CLI and HTTP surface call. Assertions are
on persisted state and on the values the cross-subsystem adapters returned, not
on mock call counts.
"""

from __future__ import annotations

import time

import pytest

from mem20edgefleetbrainz.service import FleetService, ValidationError
from mem20edgefleetbrainz.store import NotFoundError


@pytest.fixture()
def service(tmp_path):
    return FleetService(tmp_path / "fleet.db")


def register_pair(service: FleetService) -> None:
    service.register_node({
        "node_id": "a", "cpu_cores": 16, "memory_gb": 32,
        "capabilities": ["cpu"], "region": "local", "reliability": 0.99,
        "price_per_hour": 0.2, "peak_watts": 120.0,
    })
    service.register_node({
        "node_id": "b", "cpu_cores": 8, "memory_gb": 16,
        "capabilities": ["cpu"], "region": "local", "reliability": 0.9,
        "price_per_hour": 0.1, "peak_watts": 90.0,
    })


# ---------------------------------------------------------------------------
# node registry
# ---------------------------------------------------------------------------
def test_register_node_returns_real_peer_judgements(service):
    result = service.register_node({
        "node_id": "node-a", "cpu_cores": 8, "memory_gb": 16, "gpu_count": 1,
        "capabilities": ["cpu"], "region": "local", "reliability": 0.99,
    })
    assert result["ok"] is True
    assert result["version"] == 1
    assert result["node"]["node_id"] == "node-a"

    swarm = result["swarm"]
    assert swarm["ok"] is True
    assert swarm["subsystem"] == "mem20zerotouchnodeswarmz"
    assert swarm["admitted"] == 1
    assert swarm["ready"] == 1
    assert swarm["quorum"] is True
    assert swarm["preferred_node"] == "node-a"

    device = result["device"]
    assert device["ok"] is True
    assert device["tier"] == "high"
    assert device["can_run_ml"] is True
    assert device["can_render_3d"] is True
    assert device["features"]["ml_features"] is True

    quote = result["quote"]
    assert quote["ok"] is True
    assert quote["estimate"] > 0


def test_auto_capabilities_derives_tier_and_features(service):
    result = service.register_node({
        "node_id": "compiled", "cpu_cores": 8, "memory_gb": 16,
        "gpu_count": 1, "auto_capabilities": True,
    })
    capabilities = set(result["node"]["capabilities"])
    assert {"ml", "3d", "tier:high"}.issubset(capabilities)


def test_node_validation_and_conflicts(service):
    service.register_node({"node_id": "n1"})
    with pytest.raises(ValidationError):
        service.register_node({"node_id": "bad", "unknown_field": 1})
    with pytest.raises(ValidationError):
        service.register_node({"node_id": "bad", "cpu_cores": 0})
    with pytest.raises(ValidationError):
        service.set_node_status("n1", "combat")
    with pytest.raises(NotFoundError):
        service.get_node("missing")
    with pytest.raises(NotFoundError):
        service.set_node_status("missing", "online")


def test_node_status_and_delete(service):
    service.register_node({"node_id": "n1"})
    drained = service.set_node_status("n1", "draining")
    assert drained["node"]["status"] == "draining"
    assert service.get_node("n1")["status"] == "draining"
    assert service.delete_node("n1")["deleted"] is True
    with pytest.raises(NotFoundError):
        service.delete_node("n1")


# ---------------------------------------------------------------------------
# submission
# ---------------------------------------------------------------------------
def test_submit_is_idempotent_by_key(service):
    first = service.submit_workload({
        "workload_id": "w1", "cpu": 2, "memory_gb": 2, "priority": 50,
        "idempotency_key": "client-request-7",
    })
    assert first["created"] is True
    assert first["workload"]["workload_id"] == "w1"

    again = service.submit_workload({
        "workload_id": "other", "cpu": 2, "memory_gb": 2,
        "idempotency_key": "client-request-7",
    })
    assert again["created"] is False
    assert again["idempotent"] is True
    assert again["workload"]["workload_id"] == "w1"
    with pytest.raises(NotFoundError):
        service.get_workload("other")


def test_submit_reports_roaming_preview_and_compatible_nodes(service):
    service.register_node({
        "node_id": "gpu", "cpu_cores": 8, "memory_gb": 16, "gpu_count": 1,
        "capabilities": ["cpu", "gpu"], "reliability": 0.99,
    })
    service.register_node({
        "node_id": "small", "cpu_cores": 2, "memory_gb": 2,
        "capabilities": ["cpu"], "reliability": 0.9,
    })
    result = service.submit_workload({
        "workload_id": "train", "cpu": 4, "memory_gb": 8,
        "required_capabilities": ["gpu"], "priority": 70,
    })
    assert result["created"] is True
    assert result["compatible_nodes"] == ["gpu"]
    assert result["roaming"]["ok"] is True
    assert result["roaming"]["assignments"][0]["workload"] == "train"


def test_submit_rejects_bad_input_before_storing(service):
    with pytest.raises(ValidationError):
        service.submit_workload({"workload_id": "bad", "cpu": 0})
    with pytest.raises(ValidationError):
        service.submit_workload({"workload_id": "bad", "wibble": 1})
    with pytest.raises(NotFoundError):
        service.get_workload("bad")


# ---------------------------------------------------------------------------
# dispatch / completion
# ---------------------------------------------------------------------------
def test_dispatch_places_reserves_and_completes(service):
    register_pair(service)
    service.submit_workload({"workload_id": "w1", "cpu": 2, "memory_gb": 2,
                             "required_capabilities": ["cpu"], "priority": 60})
    result = service.dispatch("w1")
    assert result["dispatched"] == 1
    decision = result["decisions"][0]
    assert decision["placed"] is True
    assert decision["decision"]["chosen"] in {"a", "b"}
    assert decision["energy"]["ok"] is True
    assert decision["roaming"]["ok"] is True
    assert decision["sleep"]["ok"] is True
    assert decision["cross_system_bonuses"]

    chosen = decision["decision"]["chosen"]
    node = service.get_node(chosen)
    assert node["current_cpu"] == pytest.approx(2.0)
    workload = service.get_workload("w1")
    assert workload["state"] == "running"
    assert workload["assigned_node"] == chosen

    finished = service.complete("w1", success=True)
    assert finished["workload"]["state"] == "completed"
    assert service.get_node(chosen)["current_cpu"] == pytest.approx(0.0)


def test_dispatch_rejects_already_running_work(service):
    register_pair(service)
    service.submit_workload({"workload_id": "w1", "cpu": 1, "memory_gb": 1})
    service.dispatch("w1")
    with pytest.raises(ValidationError):
        service.dispatch("w1")


def test_completion_retries_are_bounded_and_persisted(service):
    register_pair(service)
    service.submit_workload({"workload_id": "w1", "cpu": 1, "memory_gb": 1,
                             "tolerate_fault": True})
    service.dispatch("w1")
    for attempt in range(4):
        result = service.complete("w1", success=False, reason=f"attempt {attempt}")
        workload = result["workload"]
        if workload["state"] == "queued":
            assert workload["retries"] == attempt + 1
            service.dispatch("w1")
    final = service.get_workload("w1")
    assert final["state"] == "failed"
    assert final["retries"] == 3
    node = service.get_node(final["assigned_node"] or "a")
    assert node["fault_count"] >= 1


def test_unplaceable_work_stays_queued_with_bottlenecks(service):
    service.register_node({"node_id": "cpu", "capabilities": ["cpu"],
                           "cpu_cores": 4, "memory_gb": 8})
    service.submit_workload({"workload_id": "gpu-work", "cpu": 1, "memory_gb": 1,
                             "required_capabilities": ["gpu"]})
    result = service.dispatch("gpu-work")
    assert result["dispatched"] == 0
    decision = result["decisions"][0]
    assert decision["placed"] is False
    assert any("missing capabilities gpu" in item
               for item in decision["decision"]["bottlenecks"])
    assert service.get_workload("gpu-work")["state"] == "queued"


def test_price_ceiling_and_overload_are_hard_rejections(service):
    service.register_node({"node_id": "pricey", "cpu_cores": 8, "memory_gb": 16,
                           "price_per_hour": 1.0, "capabilities": ["cpu"]})
    service.submit_workload({"workload_id": "cheap", "cpu": 1, "memory_gb": 1,
                             "max_price_per_hour": 0.25})
    assert service.dispatch("cheap")["dispatched"] == 0

    service.submit_workload({"workload_id": "huge", "cpu": 64, "memory_gb": 512})
    assert service.dispatch("huge")["dispatched"] == 0


# ---------------------------------------------------------------------------
# drain / evacuate / rebalance
# ---------------------------------------------------------------------------
def test_drain_then_evacuate_moves_running_work(service):
    register_pair(service)
    service.submit_workload({"workload_id": "w1", "cpu": 2, "memory_gb": 2,
                             "priority": 70})
    service.dispatch("w1")
    source = service.get_workload("w1")["assigned_node"]
    target = "b" if source == "a" else "a"

    drained = service.drain_node(source)
    assert drained["node"]["status"] == "draining"
    assert drained["evacuation"]["moves"][0]["to"] == target

    moved = service.evacuate(source)
    assert moved["drained"] is True
    assert moved["moves"][0]["from"] == source
    assert service.get_workload("w1")["assigned_node"] == target
    assert service.get_node(source)["status"] == "offline"


def test_evacuation_reports_stranded_work(service):
    service.register_node({"node_id": "only", "cpu_cores": 8, "memory_gb": 16})
    service.submit_workload({"workload_id": "w1", "cpu": 2, "memory_gb": 2})
    service.dispatch("w1")
    result = service.evacuate("only")
    assert result["drained"] is False
    assert result["stranded"][0]["workload_id"] == "w1"
    assert service.get_node("only")["status"] == "draining"


def test_rebalance_plans_and_applies_a_move(service):
    for node_id in ("a", "b"):
        service.register_node({"node_id": node_id, "cpu_cores": 8,
                               "memory_gb": 16, "price_per_hour": 0.1})
    service.submit_workload({"workload_id": "w1", "cpu": 3, "memory_gb": 3,
                             "priority": 50})
    service.dispatch("w1")
    source = service.get_workload("w1")["assigned_node"]
    target = "b" if source == "a" else "a"

    # Saturate the source so the rebalance threshold is exceeded even though the
    # workload itself is small. The destination stays cold.
    loaded = service.store.require_node(source)
    loaded.current_cpu = 7.5
    service.store.put_node(loaded)

    plan = service.rebalance(threshold=0.8, apply=False)
    assert plan["ok"] is True
    assert plan["applied"] == 0
    assert plan["green"]["w1"]["ok"] is True
    assert plan["roaming"]["ok"] is True
    assert len(plan["moves"]) == 1
    assert plan["moves"][0]["from"] == source
    assert plan["moves"][0]["to"] == target

    applied = service.rebalance(threshold=0.8, apply=True)
    assert applied["applied"] == 1
    assert service.get_workload("w1")["assigned_node"] == target


# ---------------------------------------------------------------------------
# sleep policy
# ---------------------------------------------------------------------------
def test_idle_nodes_sleep_for_low_priority_and_wake_for_high_priority(service):
    register_pair(service)
    idle = service.store.require_node("a")
    idle.last_seen = time.time() - 1000.0
    service.store.put_node(idle)

    service.submit_workload({"workload_id": "low", "cpu": 1, "memory_gb": 1,
                             "priority": 30})
    low = service.dispatch("low")["decisions"][0]
    assert low["sleep"]["ok"] is True
    assert "a" in low["sleep"]["sleeping"]
    assert low["woken"] == []
    assert service.get_node("a")["status"] == "sleeping"
    assert low["decision"]["chosen"] == "b"

    service.submit_workload({"workload_id": "high", "cpu": 1, "memory_gb": 1,
                             "priority": 90})
    high = service.dispatch("high")["decisions"][0]
    assert "a" in high["woken"]
    assert service.get_node("a")["status"] == "online"


def test_sleep_policy_never_sleeps_the_last_awake_node(service):
    service.register_node({"node_id": "lonely", "cpu_cores": 8, "memory_gb": 16})
    lonely = service.store.require_node("lonely")
    lonely.last_seen = time.time() - 1000.0
    service.store.put_node(lonely)

    service.submit_workload({"workload_id": "w1", "cpu": 1, "memory_gb": 1,
                             "priority": 10})
    decision = service.dispatch("w1")["decisions"][0]
    assert decision["placed"] is True
    assert service.get_node("lonely")["status"] == "online"


# ---------------------------------------------------------------------------
# observability and self-checks
# ---------------------------------------------------------------------------
def test_status_predict_energy_and_metrics(service):
    register_pair(service)
    service.submit_workload({"workload_id": "w1", "cpu": 1, "memory_gb": 1})
    status = service.status()
    assert status["ok"] is True
    assert status["health"]["nodes"] == 2
    assert status["metrics"]["nodes"] == 2
    assert status["energy"]["nodes"]
    assert status["sleep"]["ok"] is True
    assert status["roaming"]["ok"] is True
    assert isinstance(status["faults"], list)
    assert len(service.predict(3600)) == 2
    assert service.energy(12)["hours"] == 12
    assert service.metrics()["workloads"] == 1


def test_events_snapshot_and_restore_round_trip(service):
    register_pair(service)
    service.submit_workload({"workload_id": "w1", "cpu": 1, "memory_gb": 1})
    events = service.events(0, 5)
    assert events
    assert {event["kind"] for event in events} & {"node.registered",
                                                  "workload.submitted"}

    snap = service.snapshot("integration")
    service.delete_node("b")
    assert len(service.list_nodes()) == 1
    restored = service.restore(snap["snapshot_id"])
    assert restored["nodes"] == 2
    assert len(service.list_nodes()) == 2


def test_simulate_covers_six_real_scenarios(service):
    report = service.simulate()
    assert report["ok"] is True
    assert report["passed"] == report["total"] == 6
    assert "harness" not in report["scenarios"]
    for name in ("success", "malformed", "disconnection", "overload",
                 "provider_loss", "restart_recovery"):
        assert report["scenarios"][name]["ok"] is True


def test_benchmark_measures_the_real_placement_path(service):
    report = service.benchmark(iterations=5)
    assert report["ok"] is True
    assert report["iterations"] == 5
    assert report["nodes"] == 12
    assert report["ops_per_sec"] > 0
    assert report["p50_ms"] >= 0
    assert report["mean_ms"] > 0


def test_doctor_reaches_all_six_peers(service):
    report = service.doctor()
    assert report["ok"] is True
    assert len(report["ecosystem"]["reachable"]) == 6
    assert set(report["ecosystem"]["reachable"]) == {
        "mem20zerotouchnodeswarmz",
        "mem20energyawarecomputemigrationz",
        "mem20devicecapabilitycompilerz",
        "mem20hardwaremarketplacez",
        "mem20roamingworkloadschedulerz",
        "mem20modelsleepandwakesystemz",
    }
