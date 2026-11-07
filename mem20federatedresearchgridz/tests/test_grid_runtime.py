import importlib
from pathlib import Path
from mem20federatedresearchgridz.mem20federatedresearchgridz import ecosystem
from mem20federatedresearchgridz.mem20federatedresearchgridz.runtime import Engine, load_config
MOD="mem20federatedresearchgridz"
def _d(): return importlib.import_module(MOD+".domain")
def test_legacy_domain():
    m=_d()
    g=m.register_node({"nodes":[]},{"id":"n1"}); assert len(g["nodes"])==1
    g=m.register_node({"nodes":[]},{"id":"n1","status":"ready","load":0}); assert m.distribute_task(g,{"cost":1})["id"]=="n1"
    assert m.aggregate_results([1.0,2.0,3.0])==2.0
    g=m.register_node({"nodes":[]},{"id":"n1","status":"ready"}); assert m.grid_health(g)["health"]==1.0
    g=m.register_node({"nodes":[]},{"id":"n1","status":"ready","load":0,"compute":2}); assert m.federated_round(g,{"size":3})["ok"] is True
def test_ecosystem_six_peers():
    p=ecosystem.probe(); assert p["ok"] and p["count"]==6
    assert ecosystem.collective_intel()["ok"]; assert ecosystem.cognitive_search()["ok"]
    assert ecosystem.db_playground()["ok"]; assert ecosystem.crdt_merge()["ok"]
    assert ecosystem.priority_resolve()["ok"]; assert ecosystem.connector_market()["ok"]
def test_engine_search_grid_signals(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg, db_path=str(tmp_path/"g.sqlite3"))
    out=eng.execute({"query":"federated research","documents":[{"id":"d1","text":"node task"}],"nodes":[{"id":"n1","status":"ready","load":0,"compute":2}],"task":{"cost":1,"size":3,"query":"research"}}, idem="g1", timeout_ms=30000)
    assert "results" in out and "grid_health" in out and "federated_round" in out
    sig=out.get("signals") or {}
    for k in ("collective_intel","cognitive_search","db_playground","crdt_merge","priority_resolve","connector_market"):
        assert sig.get(k,{}).get("ok") is True, (k,sig.get(k))
def test_simulator_compat(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg, db_path=str(tmp_path/"s.sqlite3"))
    sim=eng.simulator(); assert all(v.get("ok") for v in sim.values()), sim
