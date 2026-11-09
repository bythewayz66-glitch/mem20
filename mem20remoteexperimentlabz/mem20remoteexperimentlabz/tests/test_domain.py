import importlib
MOD="mem20remoteexperimentlabz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_create(): e=_m().create_experiment("x",{}); assert e["status"]=="created"
def test_run(): e=_m().create_experiment("x",{"a":1}); _m().run(e, lambda p: {"score":p["a"]}); assert e["results"]["score"]==1
def test_compare(): ex=[{"results":{"score":1}},{"results":{"score":5}}]; assert _m().compare(ex)[0]["results"]["score"]==5
def test_health(): h=_m().experiment_health([{"status":"completed"},{}]); assert h["completed"]==1
def test_eco_workcell(): r=_eco().workcell_execution({"id":"e"}); assert r["ok"] and r["subsystem"]=="mem20autonomousworkcellsz"
def test_eco_swarm(): r=_eco().node_swarm(); assert r["ok"] and r["subsystem"]=="mem20zerotouchnodeswarmz"
def test_eco_events(): r=_eco().experiment_events("e",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_contain(): r=_eco().run_containment("e"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_cf(): r=_eco().scenario_compare({"s":1},{"s":2}); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_route(): r=_eco().capability_routing("k",["e"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.experiment_report(); assert rep["best"]=="b" and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
