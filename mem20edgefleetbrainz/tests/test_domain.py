"""Domain tests: the physical models and the placement decision itself.

These tests exercise real arithmetic. They do not assert that a function was
called or that a dict has a key; they assert that a hotter node is predicted to
fail sooner, that a cheaper node wins only when it is actually feasible, and
that the energy model charges the marginal draw instead of peak watts.
"""

from __future__ import annotations

import pytest

from mem20edgefleetbrainz import domain
from mem20edgefleetbrainz.domain import (
    DeviceKind,
    Node,
    NodeStatus,
    Workload,
    WorkloadState,
)


def make_node(node_id: str = "n1", **overrides) -> Node:
    values = dict(
        node_id=node_id,
        kind=DeviceKind.SERVER,
        capabilities=frozenset({"cpu"}),
        cpu_cores=8,
        memory_gb=16.0,
        gpu_count=0,
        bandwidth_mbps=1000.0,
        idle_watts=10.0,
        peak_watts=100.0,
        price_per_hour=0.0,
        reliability=0.99,
        latency_ms=5.0,
        region="local",
        status=NodeStatus.ONLINE,
        last_seen=1_000_000.0,
        uptime_s=0.0,
        temperature_c=40.0,
    )
    values.update(overrides)
    return Node(**values)


def make_workload(workload_id: str = "w1", **overrides) -> Workload:
    values = dict(
        workload_id=workload_id,
        name="test workload",
        required_capabilities=frozenset({"cpu"}),
        cpu=1.0,
        memory_gb=1.0,
        priority=50,
        duration_s=60.0,
    )
    values.update(overrides)
    return Workload(**values)


# ---------------------------------------------------------------------------
# models and validation
# ---------------------------------------------------------------------------
def test_node_rejects_invalid_physics():
    with pytest.raises(ValueError):
        Node(node_id="")
    with pytest.raises(ValueError):
        make_node(cpu_cores=0)
    with pytest.raises(ValueError):
        make_node(memory_gb=0)
    with pytest.raises(ValueError):
        make_node(idle_watts=50, peak_watts=10)
    with pytest.raises(ValueError):
        make_node(reliability=1.5)
    with pytest.raises(ValueError):
        make_node(current_cpu=-1)


def test_workload_rejects_invalid_bounds():
    with pytest.raises(ValueError):
        Workload(workload_id="")
    with pytest.raises(ValueError):
        make_workload(cpu=0)
    with pytest.raises(ValueError):
        make_workload(memory_gb=0)
    with pytest.raises(ValueError):
        make_workload(priority=101)
    with pytest.raises(ValueError):
        make_workload(duration_s=0)
    with pytest.raises(ValueError):
        make_workload(retries=-1)


def test_node_round_trips_and_reserves_capacity():
    node = make_node(capabilities={"cpu", "gpu"})
    payload = node.to_dict()
    assert payload["kind"] == "server"
    assert payload["status"] == "online"
    assert payload["capabilities"] == ["cpu", "gpu"]

    restored = Node.from_dict(payload)
    assert restored.capabilities == frozenset({"cpu", "gpu"})

    workload = make_workload(cpu=2.5, memory_gb=4.0)
    assert node.free_cpu == 8.0
    node.reserve(workload)
    assert node.free_cpu == pytest.approx(5.5)
    assert node.free_memory_gb == pytest.approx(12.0)
    # load_fraction is the max of the CPU and memory fractions: 2.5/8 > 4/16.
    assert node.load_fraction == pytest.approx(2.5 / 8.0)
    assert node.load_fraction == pytest.approx(0.3125)
    node.release(workload)
    assert node.free_cpu == 8.0
    assert node.free_memory_gb == 16.0


def test_workload_round_trips():
    workload = make_workload(required_capabilities={"cpu", "gpu"}, tags={"batch"})
    payload = workload.to_dict()
    assert payload["required_capabilities"] == ["cpu", "gpu"]
    assert payload["tags"] == ["batch"]
    assert payload["state"] == "queued"
    restored = Workload.from_dict(payload)
    assert restored.required_capabilities == frozenset({"cpu", "gpu"})
    assert restored.tags == frozenset({"batch"})


# ---------------------------------------------------------------------------
# capability, energy, cost
# ---------------------------------------------------------------------------
def test_capability_match_is_fractional_but_capped():
    node = make_node(capabilities={"cpu"})
    half = make_workload(required_capabilities={"cpu", "gpu"})
    none = make_workload(required_capabilities={"tpu"})
    empty = make_workload(required_capabilities=set())
    assert domain.capability_match(node, half) == 0.5
    assert domain.capability_match(node, none) == 0.0
    assert domain.capability_match(node, empty) == 1.0


def test_energy_charges_the_marginal_draw_not_peak_watts():
    node = make_node(idle_watts=10.0, peak_watts=100.0, current_cpu=0.0)
    full = make_workload(cpu=8.0, duration_s=3600.0)
    assert domain.estimate_energy_wh(node, full) == pytest.approx(100.0)

    idle = make_workload(cpu=0.8, duration_s=3600.0)
    assert domain.estimate_energy_wh(node, idle) == pytest.approx(10.0 + 90.0 * 0.1)

    more = make_workload(cpu=4.0, duration_s=3600.0)
    less = make_workload(cpu=1.0, duration_s=3600.0)
    assert domain.estimate_energy_wh(node, more) > domain.estimate_energy_wh(node, less)


def test_energy_uses_existing_load_as_the_floor():
    node = make_node(idle_watts=10.0, peak_watts=100.0, current_cpu=4.0)
    workload = make_workload(cpu=4.0, duration_s=3600.0)
    # base load 0.5, workload adds half of the remaining range -> 0.75
    assert domain.estimate_energy_wh(node, workload) == pytest.approx(10.0 + 90.0 * 0.75)


def test_estimate_cost_uses_hourly_price_and_duration():
    node = make_node(price_per_hour=2.0)
    workload = make_workload(duration_s=1800.0)
    assert domain.estimate_cost(node, workload) == pytest.approx(1.0)
    free = make_node(price_per_hour=0.0)
    assert domain.estimate_cost(free, workload) == 0.0


# ---------------------------------------------------------------------------
# fault prediction
# ---------------------------------------------------------------------------
def test_clean_node_is_healthy_and_bad_node_is_evacuated():
    now = 1_000_100.0
    clean = make_node(reliability=1.0, last_seen=now, temperature_c=35.0)
    good = domain.fault_risk(clean, horizon_s=3600.0, now=now)
    assert good.risk < 0.01
    assert good.recommendation == "healthy"

    bad = make_node(
        reliability=0.7,
        uptime_s=300 * 86400,
        temperature_c=90.0,
        current_cpu=8.0,
        fault_count=5,
        last_seen=now - 3600.0,
    )
    hot = domain.fault_risk(bad, horizon_s=3600.0, now=now)
    assert hot.risk > 0.6
    assert hot.recommendation == "evacuate"
    assert any("temperature" in driver for driver in hot.drivers)
    assert any("fault" in driver for driver in hot.drivers)


def test_fault_risk_grows_with_horizon_and_heat():
    now = 1_000_100.0
    warm = make_node(temperature_c=50.0, last_seen=now)
    hot = make_node(temperature_c=80.0, last_seen=now)
    hour = domain.fault_risk(warm, horizon_s=3600.0, now=now).risk
    day = domain.fault_risk(warm, horizon_s=86400.0, now=now).risk
    hot_hour = domain.fault_risk(hot, horizon_s=3600.0, now=now).risk
    assert day > hour
    assert hot_hour > hour


def test_predict_fleet_faults_sorts_riskiest_first_and_skips_offline():
    now = 1_000_100.0
    safe = make_node("safe", reliability=1.0, last_seen=now)
    risky = make_node("risky", reliability=0.6, temperature_c=85.0,
                      uptime_s=200 * 86400, last_seen=now)
    offline = make_node("off", status=NodeStatus.OFFLINE, reliability=0.1)
    forecasts = domain.predict_fleet_faults([safe, risky, offline], now=now)
    assert [f.node_id for f in forecasts] == ["risky", "safe"]
    assert forecasts[0].risk >= forecasts[1].risk


# ---------------------------------------------------------------------------
# placement
# ---------------------------------------------------------------------------
def test_score_placement_rejects_a_missing_capability():
    node = make_node(capabilities={"cpu"})
    workload = make_workload(required_capabilities={"cpu", "gpu"})
    score = domain.score_placement(node, workload)
    assert score.feasible is False
    assert score.total == 0.0
    assert "missing capabilities gpu" in score.reason


def test_score_placement_enforces_price_energy_and_deadline():
    node = make_node(price_per_hour=1.0, idle_watts=100.0, peak_watts=100.0)
    price = make_workload(max_price_per_hour=0.5)
    assert domain.score_placement(node, price).feasible is False
    assert "price" in domain.score_placement(node, price).reason

    energy = make_workload(energy_budget_wh=0.001)
    assert domain.score_placement(node, energy).feasible is False
    assert "energy" in domain.score_placement(node, energy).reason

    deadline = make_workload(duration_s=60.0, deadline_s=10.0)
    assert domain.score_placement(node, deadline).feasible is False
    assert "deadline" in domain.score_placement(node, deadline).reason


def test_score_placement_enforces_region_and_gpu():
    remote = make_node(region="eu-west")
    local = make_workload(require_local=True)
    assert domain.score_placement(remote, local).feasible is False

    no_gpu = make_node(gpu_count=0)
    needs_gpu = make_workload(gpu=1)
    assert domain.score_placement(no_gpu, needs_gpu).feasible is False


def test_feasible_score_exposes_every_component():
    node = make_node()
    workload = make_workload()
    score = domain.score_placement(node, workload)
    assert score.feasible is True
    assert 0.0 < score.total <= 1.0
    assert 0.0 <= score.confidence <= 1.0
    assert set(score.components) == set(domain._WEIGHTS)
    assert score.components["capability"] == 1.0


def test_reliability_and_latency_change_the_score():
    fast = make_node("fast", reliability=0.99, latency_ms=2.0)
    slow = make_node("slow", reliability=0.99, latency_ms=400.0)
    workload = make_workload()
    assert (domain.score_placement(fast, workload).total
            > domain.score_placement(slow, workload).total)

    reliable = make_node("reliable", reliability=0.99)
    flaky = make_node("flaky", reliability=0.8)
    assert (domain.score_placement(reliable, workload).components["reliability"]
            > domain.score_placement(flaky, workload).components["reliability"])


def test_place_workload_picks_best_and_explains_rejections():
    good = make_node("good", cpu_cores=16, memory_gb=32, reliability=0.99)
    weak = make_node("weak", cpu_cores=2, memory_gb=1, reliability=0.5)
    workload = make_workload(cpu=4.0, memory_gb=8.0)
    decision = domain.place_workload([good, weak], workload)
    assert decision.placed is True
    assert decision.chosen == "good"
    assert decision.alternatives == []
    assert any("weak:" in flow for flow in decision.bottlenecks)
    assert decision.explanation["feasible_nodes"] == 1
    assert decision.explanation["evaluated"] == 2


def test_place_workload_returns_no_choice_when_nothing_is_feasible():
    node = make_node(capabilities={"cpu"})
    workload = make_workload(required_capabilities={"gpu"})
    decision = domain.place_workload([node], workload)
    assert decision.placed is False
    assert decision.chosen is None
    assert decision.score == 0.0
    assert decision.bottlenecks


def test_cross_system_bonus_can_break_a_tie_but_not_override_feasibility():
    left = make_node("a")
    right = make_node("b")
    workload = make_workload()
    plain = domain.place_workload([left, right], workload)
    assert plain.chosen == "a"  # stable alphabetical tie-break

    flipped = domain.place_workload([left, right], workload, bonuses={"b": 0.05})
    assert flipped.chosen == "b"
    assert flipped.explanation["components"]["cross_system_bonus"] == pytest.approx(0.05)

    impossible = make_node("c", capabilities={"cpu"})
    gpu = make_workload(required_capabilities={"gpu"})
    decision = domain.place_workload([impossible], gpu, bonuses={"c": 0.09})
    assert decision.chosen is None


def test_place_workload_uses_remote_latency_for_transport_cost():
    local = make_node("local", latency_ms=5.0)
    remote = make_node("remote", latency_ms=5.0, region="eu-west")
    workload = make_workload()
    decision = domain.place_workload(
        [local, remote], workload,
        remote_latency={"remote": 450.0},
        federated_credit={"remote": 0.7},
    )
    assert decision.chosen == "local"
    assert decision.alternatives[0]["node_id"] == "remote"


# ---------------------------------------------------------------------------
# fleet-wide plans
# ---------------------------------------------------------------------------
def test_rebalance_plan_moves_work_off_a_hot_node():
    source = make_node("hot", cpu_cores=8, current_cpu=7.5)
    destination = make_node("cold", cpu_cores=8, current_cpu=0.0)
    workload = make_workload(cpu=2.0, memory_gb=2.0)
    workload.state = WorkloadState.RUNNING
    workload.assigned_node = "hot"
    plan = domain.rebalance_plan([source, destination], [workload], threshold=0.8)
    assert plan["count"] == 1
    assert plan["moves"][0]["from"] == "hot"
    assert plan["moves"][0]["to"] == "cold"
    assert plan["projected_load"]["hot"] < plan["projected_load"]["cold"] or \
        plan["projected_load"]["hot"] < 0.8


def test_rebalance_plan_does_nothing_when_every_node_is_cool():
    source = make_node("cool", current_cpu=1.0)
    destination = make_node("cooler", current_cpu=0.5)
    workload = make_workload()
    workload.state = WorkloadState.RUNNING
    workload.assigned_node = "cool"
    plan = domain.rebalance_plan([source, destination], [workload], threshold=0.8)
    assert plan["count"] == 0


def test_evacuation_plan_moves_or_reports_stranded_work():
    busy = make_node("busy", cpu_cores=8, current_cpu=4.0)
    spare = make_node("spare", cpu_cores=8, current_cpu=0.0)
    workload = make_workload(cpu=2.0)
    workload.state = WorkloadState.RUNNING
    workload.assigned_node = "busy"
    plan = domain.evacuation_plan([busy, spare], [workload], "busy")
    assert plan["drained"] is True
    assert plan["moves"][0]["to"] == "spare"

    alone = domain.evacuation_plan([busy], [workload], "busy")
    assert alone["drained"] is False
    assert alone["stranded"][0]["workload_id"] == "w1"

    with pytest.raises(KeyError):
        domain.evacuation_plan([busy], [workload], "missing")


def test_fleet_health_aggregates_capacity_and_lifecycle():
    online = make_node("online", cpu_cores=4, memory_gb=8, current_cpu=2.0,
                       current_memory_gb=4.0)
    offline = make_node("offline", status=NodeStatus.OFFLINE)
    sleeping = make_node("sleeping", status=NodeStatus.SLEEPING)
    running = make_workload("running")
    running.state = WorkloadState.RUNNING
    queued = make_workload("queued")
    failed = make_workload("failed")
    failed.state = WorkloadState.FAILED
    health = domain.fleet_health([online, offline, sleeping], [running, queued, failed])
    assert health["nodes"] == 3
    assert health["usable"] == 1
    assert health["online"] == 1
    assert health["sleeping"] == 1
    assert health["cpu_capacity"] == 4
    assert health["cpu_utilisation"] == pytest.approx(0.5)
    assert health["memory_utilisation"] == pytest.approx(0.5)
    assert health["queued"] == 1
    assert health["running"] == 1
    assert health["failed"] == 1
    assert 0.0 <= health["health"] <= 1.0


def test_energy_profile_projects_held_load_and_skips_offline():
    node = make_node("live", idle_watts=10.0, peak_watts=10.0,
                     current_cpu=0.0, price_per_hour=0.5)
    gone = make_node("gone", status=NodeStatus.OFFLINE)
    profile = domain.energy_profile([node, gone], hours=24.0)
    assert profile["total_wh"] == pytest.approx(240.0)
    assert profile["total_kwh"] == pytest.approx(0.24)
    assert profile["nodes"][0]["cost"] == pytest.approx(0.12)
    assert [row["node_id"] for row in profile["nodes"]] == ["live"]
