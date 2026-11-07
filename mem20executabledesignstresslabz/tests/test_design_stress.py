import importlib
from pathlib import Path
from mem20executabledesignstresslabz.mem20executabledesignstresslabz import ecosystem
from mem20executabledesignstresslabz.mem20executabledesignstresslabz.runtime import Engine, load_config
MOD="mem20executabledesignstresslabz"
def _d(): return importlib.import_module(MOD+".domain")

def test_legacy_domain():
    m=_d()
    r=m.stress_test({"base_load":100,"capacity":200},2.0,10); assert len(r)>0
    assert m.resilience_score([{"ok":True},{"ok":False}])==0.5
    assert m.bottleneck_analysis({"components":[{"id":"a","load":5},{"id":"b","load":10}]})[0]["id"]=="b"
    assert m.recovery_time({"redundancy":2},"crash")==15
    assert m.design_verdict([{"ok":True}]*10,0.9)["pass"] is True

def test_ecosystem_six_peers():
    p=ecosystem.probe(); assert p["ok"] and p["count"]==6
    assert ecosystem.architecture_sim({"nodes":[{"id":"a","capacity":100}]}, rps=50)["ok"]
    assert ecosystem.adversarial_qa({"feature":"x"})["ok"]
    assert ecosystem.health_nervous()["ok"]
    assert ecosystem.synthetic_eval({"id":"d"})["ok"]
    assert ecosystem.experiment_runs({"load":1})["ok"]
    assert ecosystem.intent_validate("stress test design")["ok"]

def test_engine_qa_stress_signals(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg, db_path=str(tmp_path/"s.sqlite3"))
    out=eng.execute({"tests":[{"name":"t1","pass":True}],"system":{"base_load":80,"capacity":200,"redundancy":2,"components":[{"id":"api","load":40},{"id":"db","load":60}]},"load_multiplier":1.5,"duration_s":30,"failure_type":"crash"}, idem="qa1")
    assert out["total"]==1 and out["failed"]==0
    assert "resilience" in out and "design_verdict" in out and "stress_test" in out
    sig=out.get("signals") or {}
    for k in ("architecture_sim","adversarial_qa","health_nervous","synthetic_eval","experiment_runs","intent_validate"):
        assert sig.get(k,{}).get("ok") is True, (k, sig.get(k))
    sim=eng.simulator(); assert all(v.get("ok") for v in sim.values())
