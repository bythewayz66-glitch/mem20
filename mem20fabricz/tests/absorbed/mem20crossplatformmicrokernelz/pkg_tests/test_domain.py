import importlib
MOD="mem20crossplatformmicrokernelz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_proc(): p=_m().create_process("1",5); assert p["state"]=="ready"
def test_mem(): p=_m().allocate_memory(_m().create_process("1"),[1,2]); assert len(p["memory_pages"])==2
def test_ipc(): assert _m().ipc_send("a","b","hi")["delivered"]
def test_sched(): ps=[_m().create_process("a",0),_m().create_pcess("b",1)] if False else [_m().create_process("a",0),_m().create_process("b",1)]; assert _m().schedule(ps)[0]["pid"]=="b"
def test_kill(): p=_m().kill(_m().create_process("1")); assert p["state"]=="terminated"
def test_eco_swarm(): r=_eco().node_swarm({"pid":"1"}); assert r["ok"] and r["subsystem"]=="mem20zerotouchnodeswarmz"
def test_eco_events(): r=_eco().ipc_events("x",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_contain(): r=_eco().process_containment("1"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_health(): r=_eco().kernel_health(["s"]); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_eco_route(): r=_eco().capability_routing("k",["ipc"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_locality(): r=_eco().memory_locality([1,2]); assert r["ok"] and r["subsystem"]=="mem20datalocalityoptimizerz"
def test_report_and_probe():
    m=_m(); rep=m.microkernel_report(); assert rep["ipc_delivered"] and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
