import importlib
MOD="mem20selfz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_eco_episodic(): r=_eco().episodic_memory("self"); assert r["ok"] and r["subsystem"]=="mem20episodicmemorygraphz"
def test_eco_compress(): r=_eco().context_compression("a b"); assert r["ok"] and r["subsystem"]=="mem20rewardforgez"
def test_eco_causal(): r=_eco().causal_routing({"s":1},{"s":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_events(): r=_eco().self_events("s",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().capability_routing("k",["s"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_health(): r=_eco().health_nervous(); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_report_and_probe():
    m=_m(); rep=m.self_report(); assert len(rep["peers"])>=6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert "checks" in m.probe() or "peers" in m.probe()
