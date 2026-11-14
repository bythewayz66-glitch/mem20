import importlib
MOD="mem20devicecapabilitycompilerz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_detect(): c=_m().detect_capabilities({"cpu_cores":4,"memory_gb":8}); assert c["tier"]=="high" and c["can_run_ml"]
def test_compile(): c={"can_run_ml":True,"can_render_3d":False,"tier":"mid"}; r=_m().compile_for_device("x",c); assert "ml_acceleration" in r["optimizations"]
def test_flags(): f=_m().feature_flags({"tier":"low","can_run_ml":False}); assert f["heavy_animations"] is False
def test_compat(): r=_m().compatibility({"memory_gb":2},["memory_4gb"]); assert r["compatible"] is False
def test_eco_platform(): r=_eco().platform_context(); assert r["ok"] and r["subsystem"]=="mem20crossplatformmicrokernelz"
def test_eco_place(): r=_eco().artifact_placement(0.1); assert r["ok"] and r["subsystem"]=="mem20datalocalityoptimizerz"
def test_eco_fleet(): r=_eco().device_fleet("d1"); assert r["ok"] and r["subsystem"]=="mem20zerotouchnodeswarmz"
def test_eco_match(): r=_eco().capability_match("k",["ml"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_events(): r=_eco().compile_events("c",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_health(): r=_eco().device_health(["d1"]); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_report_and_probe():
    m=_m(); rep=m.compile_report(); assert rep["compatible"] is True and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
