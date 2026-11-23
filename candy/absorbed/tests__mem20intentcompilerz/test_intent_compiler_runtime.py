from pathlib import Path
from mem20intentcompilerz.mem20intentcompilerz import ecosystem
from mem20intentcompilerz.mem20intentcompilerz.runtime import Engine, load_config
from mem20intentcompilerz.mem20intentcompilerz.domain import parse_intent, classify, compile_to_action, validate, intent_confidence

def test_legacy_domain_preserved_for_300_308():
    assert parse_intent("create user")["verb"]=="create"
    assert classify({"verb":"create","object":"x","raw":"create x"})=="mutation"
    assert compile_to_action({"verb":"list","object":"users","raw":"list users"})["action"]=="list"
    assert validate({"verb":"create","object":"x","raw":"create x"}) is True
    assert 0 <= intent_confidence({"raw":"create user now"},["create","user"]) <= 1

def test_meaningful_compose_report():
    r=ecosystem.compose_report({"text":"create deployment pipeline","resources":["ci"],"constraints":["safe"],"success_conditions":["green"]})
    assert r["integration_health"]["ok"]==6 and r["valid"] and "executable_graph" in r and "composition" in r

def test_engine_compose_and_generic(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"ic.sqlite3"))
    out=eng.execute({"text":"create user","resources":[],"constraints":[],"success_conditions":["done"]}, idem="c1")
    assert out["integration_health"]["ok"]==6 and "composition" in out
    gen=eng.execute({"goal":"compile intent","components":["parse","type","graph"]}, idem="g1")
    assert "composition" in gen and "coverage" in gen

def test_simulator_compat(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"s.sqlite3"))
    assert all(v.get("ok") for v in eng.simulator().values())
