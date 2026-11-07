import importlib
from pathlib import Path
from mem20freestackambientcomputingfabricz.mem20freestackambientcomputingfabricz import ecosystem
from mem20freestackambientcomputingfabricz.mem20freestackambientcomputingfabricz.runtime import Engine, load_config
MOD="mem20freestackambientcomputingfabricz"
def _d(): return importlib.import_module(MOD+".domain")
def test_legacy_domain():
    m=_d()
    assert m.pool_resources([{"cpu":2,"memory":4}])["cpu"]==2
    assert m.discover_services({"services":[{"id":"s","capabilities":["c"]}]},"c")[0]["id"]=="s"
    a=m.allocate({"pool":{"cpu":4,"memory":8}},{"cpu":1,"memory":2}); assert a["allocated"] is True
    assert m.fabric_health({"nodes":[{"status":"online"},{"status":"offline"}]})["health"]==0.5
    assert 0 <= m.ambient_score({"pool":{"cpu":2},"total_cpu":4}) <= 1
def test_ecosystem_six_peers():
    p=ecosystem.probe(); assert p["ok"] and p["count"]==6
    assert ecosystem.fabric_dispatch("ambient",{})["ok"]
    assert ecosystem.inference_compile({})["ok"]
    assert ecosystem.capability_market("compute")["ok"]
    assert ecosystem.microkernel({})["ok"]
    assert ecosystem.workload_identity({})["ok"]
    assert ecosystem.ambient_companion({})["ok"]
def test_engine_fabric_signals(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg, db_path=str(tmp_path/"f.sqlite3"))
    out=eng.execute({"nodes":[{"cpu":4,"memory":8,"status":"online"}],"capability":"compute","request":{"cpu":1,"memory":1},"values":[1,2,3]}, idem="f1", timeout_ms=30000)
    assert "fabric_health" in out and "allocation" in out
    sig=out.get("signals") or {}
    for k in ("fabric_dispatch","inference_compile","capability_market","microkernel","workload_identity","ambient_companion"):
        assert sig.get(k,{}).get("ok") is True, (k,sig.get(k))
def test_simulator_compat(tmp_path):
    cfg=load_config(str(Path(__file__).resolve().parents[1]/"CAPABILITY.json"))
    eng=Engine(cfg, db_path=str(tmp_path/"s.sqlite3"))
    sim=eng.simulator(); assert all(v.get("ok") for v in sim.values()), sim
