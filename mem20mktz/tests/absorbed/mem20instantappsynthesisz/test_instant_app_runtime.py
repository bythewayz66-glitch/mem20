from pathlib import Path
from mem20instantappsynthesisz.mem20instantappsynthesisz import ecosystem
from mem20instantappsynthesisz.mem20instantappsynthesisz.runtime import Engine, load_config
from mem20instantappsynthesisz.mem20instantappsynthesisz.domain import synthesize, scaffold, estimate_size, validate_spec, deploy_config

def test_legacy_domain_preserved_for_318():
    r=synthesize({"name":"app","pages":["home"],"components":["btn"]}); assert r["name"]=="app"
    assert "src" in scaffold({"files":["a.jsx"]})["dirs"]
    assert estimate_size({"pages":["home","about"],"components":["btn"]})>0
    assert validate_spec({"name":"app"})["valid"] is True
    assert deploy_config({"name":"app"},"vercel")["target"]=="vercel"

def test_meaningful_compose_report():
    r=ecosystem.compose_report({"spec":{"name":"todo","pages":["home"],"components":["list"]},"objective":"todo app"})
    assert r["integration_health"]["ok"]==6 and r["validation"]["valid"] and "scaffold" in r

def test_engine_compose_and_generic(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"ia.sqlite3"))
    out=eng.execute({"spec":{"name":"todo","pages":["home"],"components":["list"]}}, idem="c1")
    assert out["integration_health"]["ok"]==6 and "composition" in out
    gen=eng.execute({"goal":"app","components":["ui","data","api"]}, idem="g1")
    assert "composition" in gen and "coverage" in gen

def test_simulator_compat(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"s.sqlite3"))
    assert all(v.get("ok") for v in eng.simulator().values())
