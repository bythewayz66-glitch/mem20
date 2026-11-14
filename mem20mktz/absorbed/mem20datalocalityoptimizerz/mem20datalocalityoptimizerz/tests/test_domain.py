import copy, importlib
MOD="mem20datalocalityoptimizerz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_score():
    s=_m().placement_score({"latency_ms":1,"cost_per_gb":0,"capacity_gb":10,"used_gb":0},{"size_gb":1}); assert s>0
def test_optimal():
    n=_m().optimal_placement({"size_gb":1},[{"id":"a","latency_ms":10,"capacity_gb":10},{"id":"b","latency_ms":1,"capacity_gb":10}]); assert n["id"]=="b"
def test_migration():
    assert _m().migration_cost({"size_gb":10},{"egress_cost":0.1},{})==1.0
def test_locality():
    r=_m().locality_report([{"local":True},{"local":False}]); assert r["ratio"]==0.5
def test_rebalance():
    nodes=[{"id":"n1","latency_ms":1,"capacity_gb":10,"used_gb":0}]; a=_m().rebalance(nodes,[{"id":"d1","size_gb":1}]); assert a["d1"]=="n1"
def test_eco_topology(): r=_eco().node_topology([{"id":"n1"}]); assert r["ok"] and r["subsystem"]=="mem20zerotouchnodeswarmz"
def test_eco_events(): r=_eco().placement_events("x",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_contain(): r=_eco().placement_containment("n1"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_health(): r=_eco().node_health(["n1"]); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_eco_route(): r=_eco().placement_routing("k",["latency"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_cap(): r=_eco().capacity_forecast([20,25]); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_report_and_probe():
    m=_m(); rep=m.placement_report(); assert len(rep["assignments"])>0 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
