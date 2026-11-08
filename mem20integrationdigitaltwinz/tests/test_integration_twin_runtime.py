from pathlib import Path
from mem20integrationdigitaltwinz.mem20integrationdigitaltwinz import ecosystem
from mem20integrationdigitaltwinz.mem20integrationdigitaltwinz.runtime import Engine, load_config
from mem20integrationdigitaltwinz.mem20integrationdigitaltwinz.domain import create_twin, sync, simulate, drift, health

def test_legacy_domain_preserved():
    t=create_twin({"id":"s1","state":{"x":1}}); assert t["id"]=="s1"
    sync(t,{"x":5}); assert t["state"]["x"]==5
    r=simulate(t,[{"name":"a","effect":{"x":1}}]); assert len(r)==1
    assert "x" in drift(t,{"x":2})
    assert "synced" in health(t)

def test_meaningful_route_report():
    r=ecosystem.route_report({"system":{"id":"api","state":{"status":"ok"}},"scenario":[{"name":"rate_limit","effect":{"status":"throttled"}}]})
    assert r["integration_health"]["ok"]==6 and "route" in r and "simulation" in r

def test_engine_route_and_generic(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"it.sqlite3"))
    out=eng.execute({"system":{"id":"api","state":{}},"scenario":[{"name":"fail","effect":{"down":True}}]}, idem="r1")
    assert out["integration_health"]["ok"]==6 and "route" in out
    gen=eng.execute({"goal":"route request","candidates":[{"id":"a","utility":0.9}]}, idem="g1")
    assert "route" in gen and "confidence" in gen

def test_simulator_compat(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"s.sqlite3"))
    assert all(v.get("ok") for v in eng.simulator().values())
