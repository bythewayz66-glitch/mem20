from pathlib import Path
from mem20goapagentdesignerz.mem20goapagentdesignerz import ecosystem
from mem20goapagentdesignerz.mem20goapagentdesignerz.runtime import Engine, load_config
from mem20goapagentdesignerz.mem20goapagentdesignerz.domain import plan, action_cost, heuristic, validate_plan

def test_legacy_domain():
    actions=[{"name":"move","effects":{"at":"target"},"cost":1}]
    p=plan(actions,{"at":"start"},{"at":"target"}); assert p==["move"]
    assert action_cost(actions[0])==1
    assert heuristic({"at":"start"},{"at":"target"})==1
    assert validate_plan(p,actions)

def test_meaningful_report():
    r=ecosystem.goap_design_report({"actions":[{"name":"move","effects":{"at":"t"},"cost":1}],"start_state":{"at":"s"},"goal_state":{"at":"t"}})
    assert r["integration_health"]["ok"]==6 and r["valid_plan"] is True

def test_engine_search_goap_and_generic(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"g.sqlite3"))
    out=eng.execute({"actions":[{"name":"move","effects":{"at":"t"},"cost":1}],"start_state":{"at":"s"},"goal_state":{"at":"t"}}, idem="g1", timeout_ms=30000)
    assert out["integration_health"]["ok"]==6 and "results" in out
    gen=eng.execute({"query":"agent","documents":[{"name":"goap"},{"name":"db"}]}, idem="s1")
    assert "results" in gen

def test_simulator_compat(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"s.sqlite3"))
    assert all(v.get("ok") for v in eng.simulator().values())
