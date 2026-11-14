from pathlib import Path
from mem20hardwaremarketplacez.mem20hardwaremarketplacez import ecosystem
from mem20hardwaremarketplacez.mem20hardwaremarketplacez.runtime import Engine, load_config
from mem20hardwaremarketplacez.mem20hardwaremarketplacez.domain import list_hardware, search, price_estimate, transaction, marketplace_health

def test_legacy_domain_preserved():
    r = list_hardware("s", "gpu", 100); assert r["available"] is True
    ls = [list_hardware("s", "gpu", 100)]; assert len(search(ls, "gpu")) == 1
    assert price_estimate({"cores": 4, "memory_gb": 16, "storage_gb": 500, "gpu": True}) > 200
    l = list_hardware("s", "gpu", 100); assert transaction(l, "b")["status"] == "completed"
    ls = [list_hardware("s", "gpu", 100)]; assert marketplace_health(ls)["total"] == 1

def test_meaningful_match_report():
    r = ecosystem.match_report({"listings":[{"seller":"gpu-node","hardware_spec":{"cores":8,"memory_gb":16,"gpu":True},"price":50,"available":True}],"workloads":[{"id":"train","cpu":2,"memory_gb":4,"gpu":1}]})
    assert r["integration_health"]["ok"] == 6
    assert r["matches"] and r["matches"][0]["best"]["explicit_limits_ok"] is True
    assert r["swarm_availability"]["ok"] and r["scheduler_fit"]["ok"]

def test_engine_match_and_generic(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "hm.sqlite3"))
    out = eng.execute({"listings":[{"seller":"a","hardware_spec":{"cores":4,"memory_gb":8},"price":10,"available":True}],"workloads":[{"id":"w1","cpu":1,"memory_gb":1}]}, idem="m1")
    assert out["integration_health"]["ok"] == 6 and "matches" in out
    gen = eng.execute({"demand":["gpu"], "supply":["gpu node","cpu node"]}, idem="g1")
    assert "matches" in gen and "unmatched" in gen

def test_simulator_compat(tmp_path):
    cfg = load_config(str(Path(__file__).resolve().parents[1] / "CAPABILITY.json"))
    eng = Engine(cfg, db_path=str(tmp_path / "s.sqlite3"))
    res = eng.simulator()
    assert all(v.get("ok") for v in res.values())
