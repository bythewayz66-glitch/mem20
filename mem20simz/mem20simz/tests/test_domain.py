import importlib
MOD="mem20simz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_eco_cf(): r=_eco().counterfactual_sim({"x":1}); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_twin(): r=_eco().business_twin(); assert r["ok"] and r["subsystem"]=="mem20twinz"
def test_eco_causal(): r=_eco().causal_routing({"s":1},{"s":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_events(): r=_eco().sim_events("s",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().sim_routing("k",["s"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_contain(): r=_eco().sim_containment("s"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_report_and_probe():
    m=_m(); rep=m.sim_report(); assert len(rep["peers"]) >= 6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
