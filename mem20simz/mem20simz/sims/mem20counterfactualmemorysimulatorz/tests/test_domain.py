import importlib
MOD="mem20simz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_branch(): b=_m().branch({"state":{"a":1},"branch":0},{"b":2}); assert b["branch"]==1 and b["state"]["b"]==2
def test_replay(): r=_m().replay({"state":{"a":1}},[{"a":2},{"a":3}]); assert len(r)==3
def test_cf(): cf=_m().counterfactual({"state":{"a":1}},{"change":{"a":2}}); assert cf["state"]["a"]==2
def test_compare(): d=_m().compare({"state":{"a":1}},{"state":{"a":2}}); assert "a" in d
def test_prob(): assert _m().outcome_probability({"base_rate":0.5},{"effect":0.2})==0.7
def test_eco_causal(): r=_eco().causal_routing({"x":1},{"x":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_events(): r=_eco().scenario_events("x",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_recovery(): r=_eco().recovery_paths("s"); assert r["ok"] and r["subsystem"]=="mem20autonomousrecoverydirectorz"
def test_eco_healing(): r=_eco().healing_alternatives(["r"]); assert r["ok"] and r["subsystem"]=="mem20selfhealingplansz"
def test_eco_demand(): r=_eco().demand_scenarios([10,12]); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_routing(): r=_eco().scenario_routing("k",["s"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.counterfactual_report(); assert rep["outcome_probability"]>0 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
