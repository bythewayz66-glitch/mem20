import importlib
MOD="mem20pipez"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_rig(): r=_m().create_rig(["a"]); assert "a" in r["bones"]
def test_pose(): r=_m().create_rig(["a"]); _m().set_pose(r,"a",(1,2,3)); assert r["pose"]["a"]==(1,2,3)
def test_animate(): r=_m().create_rig(["a"]); p=_m().animate(r,[{"pose":{"a":(1,0,0)}}]); assert p[0]["a"]==(1,0,0)
def test_blend(): b=_m().motion_blend({"a":(10,0,0)},{"a":(0,0,0)},0.5); assert b["a"][0]==5.0
def test_health(): assert _m().rig_health(_m().create_rig(["a","b"]))["bones"]==2
def test_eco_device(): r=_eco().device_compile({"gpu":True},"x"); assert r["ok"] and r["subsystem"]=="mem20devicecapabilitycompilerz"
def test_eco_locality(): r=_eco().data_locality({"a":1},"local"); assert r["ok"] and r["subsystem"]=="mem20datalocalityoptimizerz"
def test_eco_events(): r=_eco().animation_events("a",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_contain(): r=_eco().pipeline_containment("s"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_route(): r=_eco().capability_routing("k",["a"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_config(): r=_eco().config_validation({"name":"r"}); assert r["ok"] and r["subsystem"]=="mem20deterministicconfigurationgraphz"
def test_report_and_probe():
    m=_m(); rep=m.rig_report(); assert rep["bones"]==2 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
