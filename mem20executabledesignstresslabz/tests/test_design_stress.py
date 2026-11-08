import importlib
from pathlib import Path

from mem20executabledesignstresslabz.mem20executabledesignstresslabz import ecosystem
from mem20executabledesignstresslabz.mem20executabledesignstresslabz.runtime import Engine, load_config

MOD = "mem20executabledesignstresslabz"


def _d():
    return importlib.import_module(MOD + ".domain")


def _assert_signal(signal):
    assert isinstance(signal, dict) and "subsystem" in signal and "ok" in signal
    if not signal["ok"]:
        assert "error" in signal


def test_legacy_domain():
    m = _d()
    r = m.stress_test({"base_load": 100, "capacity": 200}, 2.0, 10)
    assert len(r) > 0 and all("t" in x and "load" in x and "utilization" in x and "ok" in x for x in r)
    assert m.resilience_score([{"ok": True}, {"ok": False}]) == 0.5
    assert m.bottleneck_analysis({"components": [{"id": "a", "load": 5}, {"id": "b", "load": 10}]})[0]["id"] == "b"
    assert m.recovery_time({"redundancy": 2}, "crash") == 15
    assert m.design_verdict([{"ok": True}] * 10, 0.9)["pass"] is True


def test_ecosystem_six_peers_attempted():
    p = ecosystem.probe()
    assert set(p["checks"].keys()) == {"architecture_sim", "adversarial_qa", "health_nervous", "synthetic_eval", "experiment_runs", "intent_validate"}
    for v in p["checks"].values():
        _assert_signal(v)
    assert ecosystem.architecture_sim({"nodes": [{"id": "a", "capacity": 100}]}, rps=50)["ok"]
    assert ecosystem.adversarial_qa({"feature": "x"})["ok"]
    assert ecosystem.health_nervous()["ok"]
    assert ecosystem.synthetic_eval({"id": "d"})["ok"]
    assert ecosystem.experiment_runs({"load": 1})["ok"]
    _assert_signal(ecosystem.intent_validate("stress test design"))


def test_dependency_aware_graph_player_production_and_slo():
    m = _d()
    system = {
        "base_load": 40,
        "redundancy": 2,
        "components": [
            {"id": "edge", "capacity": 120, "load": 10},
            {"id": "api", "capacity": 100, "load": 20},
            {"id": "db", "capacity": 90, "load": 15},
        ],
        "dependencies": [{"from": "edge", "to": "api"}, {"from": "api", "to": "db"}],
        "player_cohorts": [
            {"name": "casual", "users": 50, "rps_per_user": 0.05, "burstiness": 0.2, "tolerance_ms": 900},
            {"name": "core", "users": 10, "rps_per_user": 0.2, "burstiness": 0.3, "tolerance_ms": 500},
        ],
        "production_profiles": [
            {"name": "ci", "rps": 6, "jitter": 0.1, "critical": True},
            {"name": "analytics", "rps": 4, "jitter": 0.1, "critical": False},
        ],
    }
    rep = m.run_design_graph_simulation(system, load_multiplier=1.2, duration_s=30, step_s=5, seed=7)
    assert rep["exercised_actual_graph"] is True
    assert rep["deterministic"] is True and rep["seed"] == 7
    assert rep["graph"]["edge_count"] == 2 and set(rep["graph"]["nodes"]) == {"edge", "api", "db"}
    assert rep["workload_profiles"]["player_cohorts"] and rep["workload_profiles"]["production_profiles"]
    row = rep["timeline"][1]
    assert row["workload"]["player_load"] > 0 and row["workload"]["production_load"] > 0
    expected_total = row["workload"]["technical_load"] + row["workload"]["player_load"] + row["workload"]["production_load"]
    assert abs(row["workload"]["total_load"] - expected_total) < 1e-6
    assert "error_ratio" in row["slo"] and "avg_latency_ms" in row["slo"]
    assert all(c in rep["timeline"][-1]["components"] for c in ("edge", "api", "db"))


def test_deterministic_seeded_cascading_failure_and_recovery():
    m = _d()
    system = {
        "base_load": 30,
        "redundancy": 1,
        "components": [
            {"id": "api", "capacity": 80},
            {"id": "worker", "capacity": 70},
            {"id": "db", "capacity": 60},
        ],
        "dependencies": [{"from": "api", "to": "worker"}, {"from": "worker", "to": "db"}],
        "player_cohorts": [{"name": "core", "users": 20, "rps_per_user": 0.1, "burstiness": 0.1}],
        "production_profiles": [{"name": "ci", "rps": 5, "jitter": 0.05}],
    }
    failures = [{"at_s": 10, "component": "worker", "type": "crash", "redundancy": 1}]
    a = m.run_design_graph_simulation(system, load_multiplier=1.3, duration_s=40, step_s=5, seed=42, failures=failures)
    b = m.run_design_graph_simulation(system, load_multiplier=1.3, duration_s=40, step_s=5, seed=42, failures=failures)
    assert a["timeline"] == b["timeline"], "seeded simulation must be deterministic"
    assert any(e["component"] == "worker" and e["kind"] == "failure" for e in a["failure_events"])
    assert any(e["component"] == "worker" and e["kind"] == "recovery" for e in a["recovery_events"])
    # during failure the affected component should report failed state at/after injection before recovery completes
    failed_ticks = [r for r in a["timeline"] if r["components"]["worker"]["failed"] or r["components"]["worker"]["recovery_remaining_s"] > 0]
    assert failed_ticks, "injected failure must be exercised on the graph component"
    # propagation/bottleneck evidence
    assert isinstance(a["bottlenecks"], list) and a["bottlenecks"]
    assert any(r["slo"]["error_ratio"] >= 0 or r["slo"]["avg_latency_ms"] > 0 for r in a["timeline"])


def test_scale_simulation_exercises_larger_graph():
    m = _d()
    components = [{"id": f"svc{i}", "capacity": 120 + i, "load": 5 + i} for i in range(12)]
    deps = [{"from": f"svc{i}", "to": f"svc{i+1}"} for i in range(11)]
    system = {"base_load": 60, "components": components, "dependencies": deps, "player_cohorts": [{"name": "mass", "users": 300, "rps_per_user": 0.03, "burstiness": 0.4}], "production_profiles": [{"name": "batch", "rps": 20, "jitter": 0.2}]}
    rep = m.run_design_graph_simulation(system, load_multiplier=2.5, duration_s=30, step_s=5, seed=3)
    assert rep["exercised_actual_graph"] is True
    assert len(rep["graph"]["nodes"]) == 12 and rep["graph"]["edge_count"] == 11
    assert rep["service_level"]["ticks_total"] >= 6
    assert len(rep["timeline"][-1]["components"]) == 12


def test_engine_qa_stress_signals(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "s.sqlite3"))
    out = eng.execute({
        "tests": [{"name": "t1", "pass": True}],
        "system": {"base_load": 80, "capacity": 200, "redundancy": 2, "components": [{"id": "api", "load": 40, "capacity": 140}, {"id": "db", "load": 60, "capacity": 160}], "dependencies": [{"from": "api", "to": "db"}], "player_cohorts": [{"name": "core", "users": 10, "rps_per_user": 0.1, "burstiness": 0.1}], "production_profiles": [{"name": "ci", "rps": 3, "jitter": 0.05}]},
        "load_multiplier": 1.5, "duration_s": 30, "failure_type": "crash", "seed": 1,
    }, idem="qa1")
    assert out["total"] == 1 and out["failed"] == 0
    assert "resilience" in out and "design_verdict" in out and "stress_test" in out
    sim = out.get("simulation") or {}
    assert sim.get("exercised_actual_graph") is True
    assert sim.get("workload_profiles", {}).get("player_cohorts")
    sig = out.get("signals") or {}
    for k in ("architecture_sim", "adversarial_qa", "health_nervous", "synthetic_eval", "experiment_runs", "intent_validate"):
        _assert_signal(sig.get(k, {}))
    # simulator scenarios should still pass; QA operation must not hang due to peer timeouts
    simr = eng.simulator()
    assert "success" in simr and "malformed" in simr
