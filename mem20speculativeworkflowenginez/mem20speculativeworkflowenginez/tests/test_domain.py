import importlib
MOD="mem20speculativeworkflowenginez"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_spec(): m=_m(); r=m.speculate({},["b1","b2"]); assert len(r)==2
def test_commit(): m=_m(); r=m.speculate({},["b1","b2"]); m.commit(r,"b1"); assert r[0]["status"]=="committed"
def test_roll(): m=_m(); r=m.speculate({},["b1"]); m.commit(r,"b1"); m.rollback(r); assert r[0]["status"]=="rolled_back"
def test_health(): m=_m(); r=m.speculate({},["b1"]); m.commit(r,"b1"); assert m.speculative_health(r)["committed"]==1
def test_estate_context_real_integrations(tmp_path):
    m=importlib.import_module("mem20speculativeworkflowenginez.domain"); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True
def test_eco_cf(): r=_eco().counterfactual_branch(); assert r["ok"] and r["subsystem"]=="mem20counterfactualmemorysimulatorz"
def test_eco_causal(): r=_eco().causal_routing({"b":1},{"b":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_events(): r=_eco().workflow_events("w",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().workflow_routing("k",["w"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_contain(): r=_eco().branch_containment("w"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_heal(): r=_eco().self_healing(); assert r["ok"] and r["subsystem"]=="mem20selfhealingplansz"
def test_report_and_probe():
    m=_m(); rep=m.speculative_report(); assert rep["health"]["committed"]==1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
