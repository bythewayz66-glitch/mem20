from pathlib import Path
from mem20humancapabilitysuperplatformz.mem20humancapabilitysuperplatformz import ecosystem
from mem20humancapabilitysuperplatformz.mem20humancapabilitysuperplatformz.runtime import Engine, load_config
from mem20humancapabilitysuperplatformz.mem20humancapabilitysuperplatformz.domain import assess, growth_plan, capability_matrix, team_capability, learning_recommendation

def test_legacy_domain_preserved_for_319():
    assert 0 <= assess("x", [{"weight":1,"value":0.8}]) <= 1
    assert len(growth_plan({"py":2}, {"py":5,"js":3})) == 2
    mx = capability_matrix([{"id":"u1","skills":{"py":3}}], ["py"]); assert mx["u1"]["py"] == 3
    assert team_capability({"u1":{"py":3},"u2":{"py":5}}, "py") == 4.0
    assert learning_recommendation([{"skill":"a","delta":2},{"skill":"b","delta":1}])[0]["skill"] == "a"

def test_meaningful_search_report():
    r = ecosystem.search_report({"users":[{"id":"u1","skills":{"execution":3},"evidence":[{"weight":1,"value":0.9}]}],"skills":["execution","collaboration"]})
    assert r["integration_health"]["ok"] == 6 and "results" in r and "team_capability" in r

def test_engine_search_and_generic(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path/"cp.sqlite3"))
    out = eng.execute({"users":[{"id":"u1","skills":{"execution":3},"evidence":[]}],"skills":["execution"]}, idem="c1")
    assert out["integration_health"]["ok"] == 6 and "results" in out
    gen = eng.execute({"query":"execution","documents":[{"skill":"execution"},{"skill":"art"}]}, idem="g1")
    assert "results" in gen

def test_simulator_compat(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path/"s.sqlite3"))
    assert all(v.get("ok") for v in eng.simulator().values())
