import importlib
from pathlib import Path
from mem20gameplaysystemsdataandbalancepipelinez.mem20gameplaysystemsdataandbalancepipelinez import ecosystem
from mem20gameplaysystemsdataandbalancepipelinez.mem20gameplaysystemsdataandbalancepipelinez.runtime import Engine, load_config
MOD = "mem20gameplaysystemsdataandbalancepipelinez.mem20gameplaysystemsdataandbalancepipelinez.domain"
def _d(): return importlib.import_module(MOD)
def test_legacy_domain():
    m=_d()
    assert m.collect_telemetry([{"player":"a"}])["events"]==1
    assert m.aggregate_metrics({"raw":[{"action":"jump"},{"action":"jump"}]})["action_counts"]["jump"]==2
    assert len(m.balance_tuning({"hp":10},{"hp":15}))==1
    assert m.funnel_analysis([{"name":"a","count":100},{"name":"b","count":50}])[0]["conversion"]==0.5
    assert m.pipeline_report([{"valid":True},{"valid":False}])["valid"]==1
def test_ecosystem_six_peers():
    p=ecosystem.probe(); assert p["ok"] and p["count"]==6
    for k in ("telemetry_ingest","tuning_kernel","spec_validation","narrative_system","economy_model","goap_validation"):
        assert getattr(ecosystem,k)({})["ok"]
def test_progression_compat(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"g.sqlite3"))
    out=eng.execute({"xp":300,"thresholds":[100,250,500]}, idem="p1")
    assert out["level"]==2 and "signals" not in out
def test_progression_pipeline_signals(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"g.sqlite3"))
    out=eng.execute({"xp":120,"pipeline":True,"events":[{"player":"a","action":"jump"}],"metrics":{"hp":10},"targets":{"hp":15},"data":[{"valid":True}]}, idem="b1", timeout_ms=30000)
    assert "pipeline_analysis" in out
    sig=out.get("signals") or {}
    for k in ("telemetry_ingest","tuning_kernel","spec_validation","narrative_system","economy_model","goap_validation"):
        assert sig.get(k,{}).get("ok") is True, (k,sig.get(k))
def test_simulator_compat(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"s.sqlite3"))
    assert all(v.get("ok") for v in eng.simulator().values())
