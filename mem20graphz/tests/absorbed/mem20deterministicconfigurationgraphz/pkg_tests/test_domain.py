import importlib
MOD="mem20deterministicconfigurationgraphz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_node_edge(): g={}; _m().add_node(g,"a",{"x":1}); _m().add_edge(g,"a","b"); assert "a" in g["nodes"] and ("a","b") in g["edges"]
def test_resolve(): g={}; _m().add_node(g,"p",{"a":1}); _m().add_node(g,"c",{"b":2}); _m().add_edge(g,"p","c"); r=_m().resolve(g,"c"); assert r["a"]==1 and r["b"]==2
def test_validate_ok(): g={}; _m().add_node(g,"a",{}); _m().add_node(g,"b",{}); _m().add_edge(g,"a","b"); assert _m().validate(g)["valid"] is True
def test_validate_cycle(): g={}; _m().add_node(g,"a",{}); _m().add_node(g,"b",{}); _m().add_edge(g,"a","b"); _m().add_edge(g,"b","a"); assert _m().validate(g)["valid"] is False
def test_diff(): assert "x" in _m().diff_configs({"x":1},{"x":2})
def test_eco_events(): r=_eco().config_events("x",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_contain(): r=_eco().rollout_containment("n1"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_heal(): r=_eco().healing_plans(["r"]); assert r["ok"] and r["subsystem"]=="mem20selfhealingplansz"
def test_eco_health(): r=_eco().config_health(["c"]); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_eco_dist(): r=_eco().node_distribution(["n1"]); assert r["ok"] and r["subsystem"]=="mem20zerotouchnodeswarmz"
def test_eco_route(): r=_eco().config_routing("k",["r"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.config_report(); assert rep["validation"]["valid"] and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
