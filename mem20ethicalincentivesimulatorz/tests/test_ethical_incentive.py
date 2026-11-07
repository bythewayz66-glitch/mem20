import importlib, json
from pathlib import Path
from mem20ethicalincentivesimulatorz.mem20ethicalincentivesimulatorz import ecosystem
from mem20ethicalincentivesimulatorz.mem20ethicalincentivesimulatorz.runtime import Engine, load_config

MOD="mem20ethicalincentivesimulatorz"

def _d(): return importlib.import_module(MOD+".domain")

def test_legacy_domain():
    m=_d()
    assert m.incentive(10,5)>=0
    assert 0<=m.fairness_score([1,2,3])<=1
    assert m.align_reward({"reward":10},0.5)==5.0
    assert len(m.simulate_incentives([{"value":5,"effort":3}],3))==3
    assert m.ethical_violation({"harm":1}) is True
    assert m.ethical_violation({"deceptive":True}) is True

def test_ecosystem_six_peers():
    p=ecosystem.probe(); assert p["ok"] and p["count"]==6
    assert ecosystem.outcome_simulation({"base":1,"std":0.1})["ok"]
    assert ecosystem.balance_dynamics({"damage":10,"attack_speed":1,"health":50,"income":10,"expenses":8})["ok"]
    assert ecosystem.incentive_twin({"id":"p","state":{"fairness":0.8}},{"type":"adjust"})["ok"]
    assert ecosystem.reward_composition(2)["ok"]
    assert ecosystem.reward_forge({"fairness":0.8},[0.1,0.9])["ok"]
    assert ecosystem.risk_feasibility({"name":"x","harm_risk":0.2})["ok"]

def test_engine_progression_ethical_signals(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg, db_path=str(tmp_path/"e.sqlite3"))
    out=eng.execute({"xp":50,"agents":[{"value":5,"effort":3,"id":"a"},{"value":4,"effort":4,"id":"b","ethical_score":0.8}],"rounds":3,"actions":[{"reward":10,"ethical_score":0.9},{"harm":1,"reward":5}]}, idem="t1")
    assert out["xp"]==50 and "level" in out
    assert "simulation" in out and "fairness" in out and "risk" in out
    assert "ethical_violations" in out and len(out["ethical_violations"])>=1
    sig=out.get("signals") or {}
    for k in ("outcome_simulation","balance_dynamics","incentive_twin","reward_composition","reward_forge","risk_feasibility"):
        assert sig.get(k,{}).get("ok") is True, (k, sig.get(k))
    # compatibility: built-in simulator still passes
    sim=eng.simulator()
    assert all(v.get("ok") for v in sim.values())
