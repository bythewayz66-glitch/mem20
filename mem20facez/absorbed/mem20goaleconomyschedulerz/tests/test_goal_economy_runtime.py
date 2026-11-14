from pathlib import Path
from mem20goaleconomyschedulerz.mem20goaleconomyschedulerz import ecosystem
from mem20goaleconomyschedulerz.mem20goaleconomyschedulerz.runtime import Engine, load_config
from mem20goaleconomyschedulerz.mem20goaleconomyschedulerz.domain import schedule_goals, goal_value, rebalance, progress, priority_queue

def test_legacy_domain():
    goals=[{"id":"g1","value":10,"cost":3},{"id":"g2","value":8,"cost":2}]
    r=schedule_goals(goals,4); assert "g2" in r["scheduled"]
    assert goal_value(goals[0]) > 0
    assert rebalance(goals,3)["budget"]==3
    assert progress(goals,["g1"])==0.5
    assert priority_queue(goals)[0]["id"] in ("g1","g2")

def test_meaningful_report():
    r=ecosystem.goal_economy_report({"goals":[{"id":"g1","value":10,"cost":3},{"id":"g2","value":8,"cost":2}],"budget":4})
    assert r["integration_health"]["ok"]==6
    assert "schedule" in r and "risk_flags" in r

def test_engine_schedule_goal_economy_and_generic(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"g.sqlite3"))
    out=eng.execute({"goals":[{"id":"g1","value":10,"cost":3}],"budget":5}, idem="g1", timeout_ms=30000)
    assert out["integration_health"]["ok"]==6 and "schedule" in out
    gen=eng.execute({"nodes":[{"id":"n1","capacity":2,"cost":1,"latency_ms":10}]}, idem="n1")
    assert "placement" in gen or "fallbacks" in gen

def test_simulator_compat(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"s.sqlite3"))
    assert all(v.get("ok") for v in eng.simulator().values())
