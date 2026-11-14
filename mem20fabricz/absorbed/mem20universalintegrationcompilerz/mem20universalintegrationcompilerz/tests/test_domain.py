import importlib
MOD="mem20universalintegrationcompilerz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_compile(): m=_m(); r=m.compile_integration("a","b",{"x":"y"}); assert r["compiled"] is True
def test_validate(): m=_m(); r=m.validate_mapping({"x":"y"},{"x":1},{"y":1}); assert r["valid"] is True
def test_transform(): m=_m(); r=m.transform({"x":5},{"x":"y"}); assert r["y"]==5
def test_health(): m=_m(); r=m.integration_health([{"compiled":True}]); assert r["integrations"]==1

def test_estate_context_real_integrations(tmp_path):
    m = _m()
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

def test_eco_protocol(): r=_eco().protocol_discovery(); assert r["ok"] and r["subsystem"]=="mem20protocolautodiscoveryenginez"
def test_eco_compat(): r=_eco().runtime_compat(); assert r["ok"] and r["subsystem"]=="mem20runtimecompatibilityenginez"
def test_eco_compile(): r=_eco().output_compile(); assert r["ok"] and r["subsystem"]=="mem20agentoutputcompilerz"
def test_eco_events(): r=_eco().integration_events("i",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().integration_routing("k",["i"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_contain(): r=_eco().integration_containment("i"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_report_and_probe():
    m=_m(); rep=m.integration_report(); assert rep["integration"]["compiled"] and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
