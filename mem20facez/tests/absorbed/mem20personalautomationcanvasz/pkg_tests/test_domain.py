import importlib
MOD="mem20personalautomationcanvasz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_create(): m=_m(); r=m.create_canvas("c","u"); assert r["name"]=="c"
def test_wf(): m=_m(); r=m.create_canvas("c","u"); m.add_workflow(r,{"name":"w","steps":["s1"]}); assert len(r["workflows"])==1
def test_trigger(): m=_m(); r=m.create_canvas("c","u"); m.add_trigger(r,{"event":"x"}); assert len(r["triggers"])==1
def test_run(): m=_m(); r=m.run_workflow({"name":"w","steps":["s1"]},{}); assert r["status"]=="completed"
def test_health(): m=_m(); r=m.create_canvas("c","u"); assert m.canvas_health(r)["workflows"]==0

def test_estate_context_real_integrations(tmp_path):
    m=_m(); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True

def test_eco_workcell(): r=_eco().workcell_run(); assert r["ok"] and r["subsystem"]=="mem20autonomousworkcellsz"
def test_eco_compile(): r=_eco().output_compile(); assert r["ok"] and r["subsystem"]=="mem20agentoutputcompilerz"
def test_eco_heal(): r=_eco().self_healing(); assert r["ok"] and r["subsystem"]=="mem20selfhealingplansz"
def test_eco_events(): r=_eco().canvas_events("c",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().canvas_routing("k",["c"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_causal(): r=_eco().causal_routing({"x":1},{"x":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_report_and_probe():
    m=_m(); rep=m.canvas_report(); assert rep["health"]["workflows"]==1 and rep["run"]=="completed" and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
