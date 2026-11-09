import importlib
MOD="mem20twinz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_create(): m=_m(); r=m.create_twin("u1"); assert r["user"]=="u1"
def test_observe(): m=_m(); r=m.create_twin("u1"); m.observe(r,{"action":"click"}); assert len(r["patterns"])==1
def test_suggest():
    m=_m(); r=m.create_twin("u1")
    for _ in range(3): m.observe(r,{"action":"click"})
    s=m.suggest_improvements(r); assert len(s)==1
def test_eff(): m=_m(); r=m.create_twin("u1"); m.observe(r,{"action":"click","manual":True}); assert 0<=m.efficiency_score(r)<=1
def test_health(): m=_m(); r=m.create_twin("u1"); assert "patterns" in m.twin_health(r)

def test_estate_context_real_integrations(tmp_path):
    m=_m(); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True

def test_eco_canvas(): r=_eco().automation_canvas(); assert r["ok"] and r["subsystem"]=="mem20personalautomationcanvasz"
def test_eco_workcell(): r=_eco().workcell_run(); assert r["ok"] and r["subsystem"]=="mem20autonomousworkcellsz"
def test_eco_compile(): r=_eco().output_compile(); assert r["ok"] and r["subsystem"]=="mem20agentoutputcompilerz"
def test_eco_episodic(): r=_eco().episodic_memory(); assert r["ok"] and r["subsystem"]=="mem20episodicmemorygraphz"
def test_eco_events(): r=_eco().twin_events("t",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().twin_routing("k",["t"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.workflow_twin_report(); assert rep["suggestions"]==1 and rep["health"]["patterns"]==3 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
