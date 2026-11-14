import importlib
MOD="mem20realitytosoftwarecompilerz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_ingest(): assert _m().ingest("name: x")["name"]=="x"
def test_compile(): c=_m().compile_to_code({"name":"demo"}); assert "Demo" in c
def test_validate(): assert _m().validate_spec({"name":"x"})["valid"] is True
def test_diff(): d=_m().diff_spec({"a":1},{"a":2}); assert "a" in d
def test_health(): assert _m().compile_health({"name":"x"})["valid"] is True
def test_eco_foundry(): r=_eco().software_foundry({"name":"x"}); assert r["ok"] and r["subsystem"]=="mem20autonomoussoftwarefoundryz"
def test_eco_config(): r=_eco().config_validation({"name":"x"}); assert r["ok"] and r["subsystem"]=="mem20deterministicconfigurationgraphz"
def test_eco_events(): r=_eco().compile_events("c",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_causal(): r=_eco().causal_routing({"q":1},{"q":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_contain(): r=_eco().compile_containment("x"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_route(): r=_eco().capability_routing("k",["c"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.compiler_report(); assert rep["valid"] is True and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
