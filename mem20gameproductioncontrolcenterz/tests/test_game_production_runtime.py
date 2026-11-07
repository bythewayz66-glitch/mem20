import importlib
from pathlib import Path
from mem20gameproductioncontrolcenterz.mem20gameproductioncontrolcenterz import ecosystem
from mem20gameproductioncontrolcenterz.mem20gameproductioncontrolcenterz.runtime import Engine, load_config

MOD = "mem20gameproductioncontrolcenterz.mem20gameproductioncontrolcenterz.domain"
def _d(): return importlib.import_module(MOD)

def test_legacy_domain_preserved():
    m = _d()
    r = m.sprint_plan([{"id":"t1","effort":3},{"id":"t2","effort":4}], 5); assert len(r) >= 1
    b = m.burndown([{"id":"t1","effort":3}], ["t1"]); assert b["done"] == 3
    ms = m.milestone_status([{"id":"m1","due_day":5}], 3); assert ms[0]["status"] == "on_track"
    assert 0 <= m.risk_score({"scope_creep": True, "team_size": 2, "budget_ratio": 1.2}) <= 1
    assert m.production_health([{"done": True}, {"done": False}]) == 0.5

def test_meaningful_production_control_report():
    # Exercises real domain composition + 6 peer integrations (covered for criterion 6)
    r = ecosystem.production_control_report({
        "tasks": [{"id":"t1","effort":3},{"id":"t2","effort":2}],
        "capacity": 5, "today": 1,
        "milestones": [{"id":"m1","due_day":5}],
        "project": {"team_size": 4, "budget_ratio": 0.9, "scope_creep": False},
        "sprints": [{"done": True}, {"done": False}],
        "completed_ids": ["t1"],
        "team": [{"id":"d1","status":"online"},{"id":"d2","status":"online"}],
        "budget": {"arpu": 10, "months": 12, "margin": 0.7, "spend": 500, "acquired": 10},
    })
    assert r["burndown"]["done"] == 3
    assert r["milestones"][0]["status"] == "on_track"
    assert r["integration_health"]["ok"] == 6 and r["integration_health"]["total"] == 6
    assert "adjusted" in r["risk"] and isinstance(r["production_health"], (int, float))
    # peer-derived sections are meaningful (not empty probes)
    assert r["integrations"]["team_capacity"]["ok"] and r["integrations"]["cost_projection"]["ok"]
    assert r["integrations"]["release_readiness"]["ok"] and r["integrations"]["resilience_assessment"]["ok"]

def test_ecosystem_probe():
    p = ecosystem.probe(); assert p["ok"] and p["count"] == 6

def test_engine_simulate_backward_compat_and_production(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "p.sqlite3"))
    # backward compat: scenarios only
    out = eng.execute({"baseline": 1, "scenarios": [{"name":"baseline","multiplier":1}]}, idem="s1")
    assert "scenarios" in out and out["scenarios"][0]["name"] == "baseline"
    # meaningful production control
    out2 = eng.execute({"baseline": 1, "production": True, "tasks":[{"id":"t1","effort":2}], "capacity":5, "today":0, "milestones":[{"id":"m1","due_day":3}], "project":{"team_size":5}}, idem="p1", timeout_ms=30000)
    assert "scenarios" in out2 and "production_control" in out2
    assert out2["production_control"]["integration_health"]["ok"] == 6

def test_simulator_compat(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "sim.sqlite3"))
    assert all(v.get("ok") for v in eng.simulator().values())
