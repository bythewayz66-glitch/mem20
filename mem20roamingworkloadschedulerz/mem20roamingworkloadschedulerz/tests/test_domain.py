import importlib
MOD="mem20roamingworkloadschedulerz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_schedule(): nodes=[{"id":"a","load":0},{"id":"b","load":5}]; a=_m().schedule([{"id":"w","cost":1}],nodes); assert a[0]["node"]=="a"
def test_migrate(): m=_m().migrate("w","a","b"); assert m["from"]=="a" and m["to"]=="b"
def test_load(): assert _m().node_load([{"id":"n","load":3}])["n"]==3
def test_health(): h=_m().scheduler_health([{"load":1},{"load":2}]); assert h["total_load"]==3
def test_eco_swarm(): r=_eco().node_swarm(); assert r["ok"] and r["subsystem"]=="mem20zerotouchnodeswarmz"
def test_eco_workcell(): r=_eco().workcell_queue({"id":"w"}); assert r["ok"] and r["subsystem"]=="mem20autonomousworkcellsz"
def test_eco_forecast(): r=_eco().capacity_forecast([1,2]); assert r["ok"] and r["subsystem"]=="mem20demandforecastandcapacitybrainz"
def test_eco_events(): r=_eco().schedule_events("s",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_contain(): r=_eco().migration_containment("w"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_route(): r=_eco().scheduler_routing("k",["s"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.scheduler_report(); assert rep["assignments"]==2 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
