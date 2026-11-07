import importlib
from pathlib import Path
from mem20executiondigitaltwinz.mem20executiondigitaltwinz import ecosystem
from mem20executiondigitaltwinz.mem20executiondigitaltwinz.runtime import Engine, load_config

MOD = "mem20executiondigitaltwinz"
def _d(): return importlib.import_module(MOD + ".domain")

def test_legacy_domain_preserved():
    m = _d()
    t = m.create_twin({"id": "p1", "state": {"x": 1}})
    assert t["id"] == "p1"
    m.sync_twin(t, {"x": 5}); assert t["state"]["x"] == 5
    r = m.simulate(t, [{"name": "a", "effect": {"x": 1}}]); assert len(r) == 1
    p = m.predict_outcome(m.create_twin({"id": "p", "metrics": {"success_rate": 0.7}}), {"impact": 0.1})
    assert 0 <= p <= 1
    assert "x" in m.drift(m.create_twin({"id": "p", "state": {"x": 1}}), {"x": 2})

def test_ecosystem_six_peers():
    p = ecosystem.probe(); assert p["ok"] and p["count"] == 6
    assert ecosystem.workflow_twin({"id": "u"})["ok"]
    assert ecosystem.integration_twin({"id": "s"}, {"q": 1})["ok"]
    assert ecosystem.time_machine({"x": 1})["ok"]
    assert ecosystem.counterfactual_sim({"state": {"x": 1}})["ok"]
    assert ecosystem.customer_twin({"id": "c"})["ok"]
    assert ecosystem.event_lattice([])["ok"]

def test_engine_forecast_twin_signals(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "t.sqlite3"))
    out = eng.execute({"process": {"id": "wf", "state": {"progress": 1}, "metrics": {"success_rate": 0.7}},
                       "real_state": {"progress": 2}, "actions": [{"name": "advance", "effect": {"progress": 1}, "impact": 0.05}],
                       "series": [1, 2, 3], "steps": 2}, idem="t1", timeout_ms=5000)
    assert "slope" in out and "forecast" in out and "confidence" in out
    assert "twin" in out and "simulation" in out and "drift" in out
    sig = out.get("signals") or {}
    for k in ("workflow_twin", "integration_twin", "time_machine", "counterfactual_sim", "customer_twin", "event_lattice"):
        assert sig.get(k, {}).get("ok") is True, (k, sig.get(k))

def test_engine_simulator_compat(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "s.sqlite3"))
    sim = eng.simulator()
    assert all(v.get("ok") for v in sim.values()), sim
