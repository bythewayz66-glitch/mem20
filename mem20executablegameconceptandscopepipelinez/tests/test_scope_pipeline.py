import importlib
from pathlib import Path
from mem20executablegameconceptandscopepipelinez.mem20executablegameconceptandscopepipelinez import ecosystem
from mem20executablegameconceptandscopepipelinez.mem20executablegameconceptandscopepipelinez.runtime import Engine, load_config

MOD = "mem20executablegameconceptandscopepipelinez"
def _d(): return importlib.import_module(MOD + ".domain")

def test_legacy_domain_preserved():
    m = _d()
    assert m.concept_score({"innovation": 8, "market_fit": 7, "feasibility": 6}) > 0
    s = m.scope_estimate({"features": ["a", "b", "c"], "complexity": "medium"})
    assert s["weeks"] == 6 and s["features"] == 3
    f = m.feasibility_check({"features": ["a"], "complexity": "low"}, budget_weeks=10)
    assert f["feasible"] is True
    assert "high complexity" in m.risk_assessment({"complexity": "high", "market_fit": 3, "team_size": 2})
    assert m.pipeline_stage({"innovation": 9, "market_fit": 9, "feasibility": 9}) in ("greenlit", "viable", "risky", "rethink")

def test_ecosystem_six_peers():
    p = ecosystem.probe(); assert p["ok"] and p["count"] == 6
    c = {"name": "demo", "innovation": 6, "market_fit": 6, "feasibility": 6, "features": ["core"], "complexity": "medium"}
    assert ecosystem.production_control(c)["ok"]
    assert ecosystem.studio_ops(c)["ok"]
    assert ecosystem.growth_feasibility(c)["ok"]
    assert ecosystem.software_foundry(c)["ok"]
    assert ecosystem.game_studio(c)["ok"]
    assert ecosystem.microsaas_foundry(c)["ok"]

def test_engine_graph_scope_signals(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "g.sqlite3"))
    # explicit scope request exercises 6 peer signals (criterion 6 coverage)
    out = eng.execute({"concept": {"name": "demo", "innovation": 7, "market_fit": 6, "feasibility": 6, "features": ["core", "ui"], "complexity": "medium"}, "budget_weeks": 24}, idem="scope1", timeout_ms=5000)
    assert out["pipeline_stage"] in ("greenlit", "viable", "risky", "rethink", "prototype", "vertical_slice", "pre_production", "concept")
    assert "concept_score" in out and "scope" in out and "feasibility" in out
    assert out.get("nodes", 0) == 0 and "degree" in out and "hubs" in out
    sig = out.get("signals") or {}
    for k in ("production_control", "studio_ops", "growth_feasibility", "software_foundry", "game_studio", "microsaas_foundry"):
        assert sig.get(k, {}).get("ok") is True, (k, sig.get(k))

def test_engine_graph_simulator_compat(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "s.sqlite3"))
    sim = eng.simulator()
    assert all(v.get("ok") for v in sim.values()), sim
