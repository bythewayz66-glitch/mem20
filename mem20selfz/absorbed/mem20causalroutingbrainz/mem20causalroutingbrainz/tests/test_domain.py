import importlib
MOD="mem20causalroutingbrainz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_effect(): assert _m().causal_effect([1,1],[0,0])==1.0
def test_route(): assert isinstance(_m().route_by_cause({"a":1},{"a":2}),float)
def test_adjust(): assert _m().confounder_adjust(1.0,0.2)==0.8
def test_intervention(): assert _m().intervention_value(1.0,1.5)==0.5
def test_graph(): assert "a" in _m().causal_graph([("a","b")])
def test_ecosystem_counterfactual(): r=_eco().counterfactual_route({"x":1},{"effect":0.1}); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_ecosystem_events(): r=_eco().route_events("x",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_ecosystem_capability(): r=_eco().capability_target("k",["r"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_ecosystem_failure(): r=_eco().failure_signal("r"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_ecosystem_health(): r=_eco().health_signal(["a"]); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_ecosystem_nodes(): r=_eco().node_targets({}); assert r["ok"] and r["subsystem"]=="mem20zerotouchnodeswarmz"
def test_report_and_probe():
    m=_m(); rep=m.routing_report(); assert len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
