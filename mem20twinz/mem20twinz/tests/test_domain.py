import importlib
MOD="mem20twinz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_eco_exec(): r=_eco().execution_twin(); assert r["ok"] and r["subsystem"]=="mem20executiondigitaltwinz"
def test_eco_biz(): r=_eco().business_twin(); assert r["ok"] and r["subsystem"]=="mem20realtimebusinesstwinz"
def test_eco_cf(): r=_eco().counterfactual_sim(); assert r["ok"] and r["subsystem"]=="mem20counterfactualmemorysimulatorz"
def test_eco_events(): r=_eco().twin_events("t",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().twin_routing("k",["t"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_causal(): r=_eco().causal_routing({"x":1},{"x":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_report_and_probe():
    m=_m(); rep=m.twin_report(); assert len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
