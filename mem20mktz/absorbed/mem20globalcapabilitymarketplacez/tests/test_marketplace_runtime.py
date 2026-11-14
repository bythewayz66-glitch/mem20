import importlib
from pathlib import Path
from mem20globalcapabilitymarketplacez.mem20globalcapabilitymarketplacez import ecosystem
from mem20globalcapabilitymarketplacez.mem20globalcapabilitymarketplacez.runtime import Engine, load_config
MOD = "mem20globalcapabilitymarketplacez.mem20globalcapabilitymarketplacez.domain"
def _d(): return importlib.import_module(MOD)
def test_legacy_domain():
    m=_d()
    l=m.list_capability("s","workflow ai",10); assert l["available"]
    assert m.search_marketplace([l],"workflow")
    got=m.match([l],{"capability":"workflow"}); assert got and got["seller"]=="s"
    tx=m.transaction(got,"b"); assert tx["status"]=="completed"
    h=m.marketplace_health([l]); assert h["available"]==1
def test_meaningful_enrich():
    r=ecosystem.marketplace_enrich({"listings":[{"seller":"s1","capability":"workflow ai","price":10,"available":True}],"requirement":{"capability":"workflow"},"buyer":"b1","query":"workflow"})
    assert r["integration_health"]["ok"]==6
    assert r["trial_ready"] is True
    assert r["transaction"]["trial_ready"] is True
def test_engine_match_marketplace_and_generic(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"m.sqlite3"))
    out=eng.execute({"listings":[{"seller":"s1","capability":"workflow ai","price":10,"available":True}],"requirement":{"capability":"workflow"},"buyer":"b1"}, idem="m1", timeout_ms=30000)
    assert out["integration_health"]["ok"]==6 and out["match"]["seller"]=="s1"
    gen=eng.execute({"demand":["ai workflow"],"supply":[{"capability":"workflow ai"},{"capability":"db"}]}, idem="g1")
    assert "matches" in gen
def test_simulator_compat(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg,db_path=str(tmp_path/"s.sqlite3"))
    assert all(v.get("ok") for v in eng.simulator().values())
