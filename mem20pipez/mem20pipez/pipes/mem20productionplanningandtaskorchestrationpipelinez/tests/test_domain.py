import importlib
MOD="mem20pipez"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_plan(): p=_m().create_plan([{"id":"a","effort":3,"priority":1}], capacity=5); assert len(p["scheduled"])==1
def test_orchestrate(): a=_m().orchestrate([{"id":"t1"}],["ag1"]); assert a[0]["agent"]=="ag1"
def test_bottleneck(): b=_m().bottleneck([{"id":"a","effort":1},{"id":"b","effort":5}]); assert b["id"]=="b"
def test_health(): h=_m().pipeline_health([{"status":"done"},{}]); assert h["progress"]==0.5
def test_eco_workcells(): r=_eco().workcells({"id":"t1"}); assert r["ok"] and r["subsystem"]=="mem20autonomousworkcellsz"
def test_eco_swarm(): r=_eco().node_swarm(); assert r["ok"] and r["subsystem"]=="mem20zerotouchnodeswarmz"
def test_eco_cap(): r=_eco().capacity_plan([5,6]); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_contain(): r=_eco().task_containment("t1"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_events(): r=_eco().orchestration_events("o",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().capability_routing("k",["o"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.orchestration_report(); assert rep["scheduled"]>=1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
