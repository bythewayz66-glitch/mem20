import importlib
MOD="mem20visualdataflowcomposerz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_create(): m=_m(); r=m.create_pipeline("p1"); assert r["name"]=="p1"
def test_node(): m=_m(); r=m.create_pipeline("p1"); n=m.add_node(r,"source"); assert n["type"]=="source"
def test_conn(): m=_m(); r=m.create_pipeline("p1"); a=m.add_node(r,"a"); b=m.add_node(r,"b"); m.connect(r,a["id"],b["id"]); assert len(r["edges"])==1
def test_exec(): m=_m(); r=m.create_pipeline("p1"); m.add_node(r,"a"); res=m.execute(r,{},lambda n,d: 42); assert len(res)==1
def test_health(): m=_m(); r=m.create_pipeline("p1"); m.add_node(r,"a"); assert m.pipeline_health(r)["nodes"]==1

def test_estate_context_real_integrations(tmp_path):
    m = _m()
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["composition_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

def test_eco_blackboard(): r=_eco().blackboard_state(); assert r["ok"] and r["subsystem"]=="mem20visualagentblackboardz"
def test_eco_workcell(): r=_eco().workcell_execute(); assert r["ok"] and r["subsystem"]=="mem20autonomousworkcellsz"
def test_eco_compile(): r=_eco().output_compile(); assert r["ok"] and r["subsystem"]=="mem20agentoutputcompilerz"
def test_eco_events(): r=_eco().flow_events("f",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().flow_routing("k",["f"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_causal(): r=_eco().causal_routing({"x":1},{"x":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_report_and_probe():
    m=_m(); rep=m.flow_report(); assert rep["health"]["nodes"]==1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
