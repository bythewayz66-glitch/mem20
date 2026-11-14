from pathlib import Path
from mem20hotswappableservicefoundationz.mem20hotswappableservicefoundationz import ecosystem
from mem20hotswappableservicefoundationz.mem20hotswappableservicefoundationz.runtime import Engine, load_config
from mem20hotswappableservicefoundationz.mem20hotswappableservicefoundationz.domain import register_service, swap, health, rollback, list_services

def test_legacy_domain_preserved_for_317():
    r = register_service({}, "svc", "impl1"); assert "svc" in r["services"]
    swap(r, "svc", "impl2"); assert r["services"]["svc"]["version"] == 2
    assert health(r)["active"] == 1
    rollback(r, "svc"); assert r["services"]["svc"]["version"] == 1
    assert "svc" in list_services(r)

def test_meaningful_analyze_report():
    r = ecosystem.analyze_report({"service":"api","op":"swap","impl":"v2","config":{"deps":["runtime"]}})
    assert r["integration_health"]["ok"] == 6 and r["swap_ready"] is True
    assert r["operation"]["ok"] is True and "domain_health" in r

def test_engine_analyze_and_generic(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path/"hs.sqlite3"))
    out = eng.execute({"service":"api","op":"register","impl":"v1"}, idem="a1")
    assert out["integration_health"]["ok"] == 6
    gen = eng.execute({"values":[1,2,3]}, idem="g1")
    assert "confidence" in gen or "decision" in gen

def test_simulator_compat(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path/"s.sqlite3"))
    assert all(v.get("ok") for v in eng.simulator().values())
