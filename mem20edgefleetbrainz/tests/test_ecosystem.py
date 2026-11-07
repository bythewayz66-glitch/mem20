"""Ecosystem tests: all six peers return real values.

Every assertion reads a number or classification the *other* subsystem
computed. If a peer is renamed, its domain module breaks, or the adapter stops
calling it, these tests fail instead of silently passing on an import.
"""

from __future__ import annotations

import time

import pytest

from mem20edgefleetbrainz import ecosystem


def fleet_node(node_id: str = "n1", **overrides) -> dict:
    values = {
        "node_id": node_id,
        "kind": "server",
        "cpu_cores": 8,
        "memory_gb": 16.0,
        "gpu_count": 0,
        "storage_gb": 512.0,
        "capabilities": ["cpu"],
        "reliability": 0.98,
        "latency_ms": 5.0,
        "idle_watts": 12.0,
        "peak_watts": 120.0,
        "price_per_hour": 0.2,
        "carbon_g_per_kwh": 380.0,
        "region": "local",
        "status": "online",
        "last_seen": time.time(),
    }
    values.update(overrides)
    return values


def test_swarm_admission_uses_capacity_and_capability():
    preferred = fleet_node("strong", cpu_cores=32, capabilities=["cpu", "gpu"])
    peer = fleet_node("weak", cpu_cores=4)
    result = ecosystem.swarm_admission(
        preferred, peers=[peer], capability="gpu", urgency=1.0)
    assert result["ok"] is True
    assert result["subsystem"] == "mem20zerotouchnodeswarmz"
    # Both nodes join the swarm, but only the GPU node is *ready* for a GPU task.
    assert result["admitted"] == 2
    assert result["ready"] == 1
    assert result["quorum"] is True
    assert result["preferred_node"] == "strong"
    assert result["preferred_score"] > 0


def test_energy_plan_ranks_the_low_power_node_and_prices_migration():
    green = fleet_node("green", peak_watts=40.0, cpu_cores=8)
    dirty = fleet_node("dirty", peak_watts=400.0, cpu_cores=8)
    workload = {"workload_id": "w1", "cpu": 4.0, "duration_s": 600.0}
    result = ecosystem.energy_plan([dirty, green], workload, source=dirty)
    assert result["ok"] is True
    assert result["subsystem"] == "mem20energyawarecomputemigrationz"
    assert result["greenest"] == "green"
    assert result["energy_cost"] >= 0.0
    assert result["carbon_g"] > 0.0
    assert result["workload_size"] == 40.0
    assert isinstance(result["migration"], dict)
    assert "migrate" in result["migration"]


def test_energy_plan_handles_an_empty_fleet():
    result = ecosystem.energy_plan([], {"workload_id": "w"})
    assert result["ok"] is True
    assert result["greenest"] is None
    assert result["energy_cost"] == 0.0


def test_device_fit_derives_tier_and_reports_missing_features():
    weak = {"cpu_cores": 1, "gpu_count": 0, "memory_gb": 2.0,
            "storage_gb": 32.0, "network": "wifi"}
    result = ecosystem.device_fit(weak, requirements=["gpu", "ml", "memory_4gb"])
    assert result["ok"] is True
    assert result["subsystem"] == "mem20devicecapabilitycompilerz"
    assert result["tier"] == "low"
    assert result["can_run_ml"] is False
    assert result["can_render_3d"] is False
    assert result["compatible"] is False
    assert set(result["missing"]) == {"gpu", "ml", "memory_4gb"}
    assert result["features"]["heavy_animations"] is False

    strong = {"cpu_cores": 8, "gpu_count": 1, "memory_gb": 16.0,
              "storage_gb": 512.0, "network": "ethernet"}
    fit = ecosystem.device_fit(strong, requirements=["gpu", "ml", "memory_4gb"])
    assert fit["tier"] == "high"
    assert fit["can_run_ml"] is True
    assert fit["can_render_3d"] is True
    assert fit["compatible"] is True
    assert fit["features"]["3d_view"] is True


def test_hardware_quote_prices_the_node_and_searches_inventory():
    node = fleet_node("n1", cpu_cores=8, memory_gb=16.0, storage_gb=512.0,
                      gpu_count=1, kind="server", price_per_hour=0.2)
    peer = fleet_node("n2", kind="server", price_per_hour=0.3, status="online")
    result = ecosystem.hardware_quote(node, listings=[node, peer])
    assert result["ok"] is True
    assert result["subsystem"] == "mem20hardwaremarketplacez"
    # 8*50 + 16*10 + 512*0.1 + 200 GPU = 811.2
    assert result["estimate"] == pytest.approx(811.2)
    assert result["matches"] >= 1
    assert result["market"]["total"] == 2
    assert result["market"]["available"] == 2


def test_roaming_plan_assigns_by_load_and_reports_health():
    workloads = [
        {"workload_id": "w1", "cpu": 2.0},
        {"workload_id": "w2", "cpu": 1.0},
    ]
    nodes = [
        {"node_id": "a", "current_cpu": 1.0},
        {"node_id": "b", "current_cpu": 0.0},
    ]
    result = ecosystem.roaming_plan(workloads, nodes)
    assert result["ok"] is True
    assert result["subsystem"] == "mem20roamingworkloadschedulerz"
    assert [item["workload"] for item in result["assignments"]] == ["w1", "w2"]
    # w1 goes to the idle node b; w2 then goes to a because b is loaded.
    assert result["assignments"][0]["node"] == "b"
    assert result["assignments"][1]["node"] == "a"
    # Loads are reported after assignment: a started at 1 and took w2 (1),
    # b started at 0 and took w1 (2).
    assert result["loads"] == {"a": 2.0, "b": 2.0}
    assert result["health"]["nodes"] == 2
    assert result["health"]["total_load"] == 4.0


def test_sleep_plan_separates_idle_from_recent_nodes():
    now = time.time()
    cases = [
        fleet_node("idle", last_seen=now - 1200.0),
        fleet_node("active", last_seen=now),
    ]
    result = ecosystem.sleep_plan(cases, idle_threshold=300.0, now=now)
    assert result["ok"] is True
    assert result["subsystem"] == "mem20modelsleepandwakesystemz"
    assert result["sleeping"] == ["idle"]
    assert result["awake"] == ["active"]
    assert result["health"] == {"total": 2, "sleeping": 1, "awake": 1}


def test_probe_reaches_every_peer():
    report = ecosystem.probe()
    assert report["ok"] is True
    assert set(report["checks"]) == {
        "mem20zerotouchnodeswarmz",
        "mem20energyawarecomputemigrationz",
        "mem20devicecapabilitycompilerz",
        "mem20hardwaremarketplacez",
        "mem20roamingworkloadschedulerz",
        "mem20modelsleepandwakesystemz",
    }
    assert len(report["reachable"]) == 6
