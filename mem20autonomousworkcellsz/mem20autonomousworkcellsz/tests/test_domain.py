import importlib
MOD="mem20autonomousworkcellsz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")

def test_cell():
    m=_m(); c=m.create_cell("a",4); m.enqueue(c,{"id":1}); m.assign_workers(c,["w1"])
    r=m.process_next(c); assert r["worker"]=="w1"

def test_throughput(): assert _m().throughput({"completed":60},60)==60.0
def test_health(): assert _m().cell_health({"queue":[1,2],"capacity":4,"completed":0})["queue_depth"]==2
def test_core_ops():
    m=_m(); c=m.create_cell("b",2); m.enqueue(c,{"id":1}); m.enqueue(c,{"id":2}); m.assign_workers(c,["w1","w2"])
    assert m.process_next(c)["task"]["id"]==1; h=m.cell_health(c); assert h["completed"]==1

def test_ecosystem_swarm_workers(): r=_eco().swarm_workers({"id":"t1"}); assert r["ok"] and r["subsystem"]=="mem20zerotouchnodeswarmz"; assert r["assigned"] is True
def test_ecosystem_capability_routing(): r=_eco().capability_routing("k",["cpu"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"; assert r["owner"] is not None
def test_ecosystem_work_events(): r=_eco().work_events("x",{"a":1}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"; assert r["published"]==1
def test_ecosystem_cell_containment(): r=_eco().cell_containment("c"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_ecosystem_focus_priority(): r=_eco().focus_priority({"priority":1,"distractions":0}); assert r["ok"] and r["subsystem"]=="mem20mixedinitiativefocusenginez"; assert "score" in r
def test_ecosystem_capacity_forecast(): r=_eco().capacity_forecast([2,3,4],4); assert r["ok"] and r["subsystem"]=="mem20demandforecastandcapacitybrainz"; assert r["point"] is not None

def test_workcell_report_and_probe():
    m=_m(); rep=m.workcell_report(); assert rep["processed"] is True and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
