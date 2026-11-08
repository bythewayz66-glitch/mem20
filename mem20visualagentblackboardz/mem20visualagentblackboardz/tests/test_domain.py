import importlib
MOD="mem20visualagentblackboardz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_create(): m=_m(); r=m.create_blackboard("bb"); assert r["name"]=="bb"
def test_post(): m=_m(); r=m.create_blackboard("bb"); m.post(r,"a1","item"); assert len(r["items"])==1
def test_read(): m=_m(); r=m.create_blackboard("bb"); m.post(r,"a1","item"); assert len(m.read(r))==1
def test_clear(): m=_m(); r=m.create_blackboard("bb"); m.post(r,"a1","item"); m.clear(r); assert len(r["items"])==0
def test_health(): m=_m(); r=m.create_blackboard("bb"); m.post(r,"a1","item"); assert m.blackboard_health(r)["items"]==1

def test_estate_context_real_integrations(tmp_path):
    m = _m()
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

def test_eco_workcell(): r=_eco().workcell_dispatch(); assert r["ok"] and r["subsystem"]=="mem20autonomousworkcellsz"
def test_eco_compile(): r=_eco().output_compile(); assert r["ok"] and r["subsystem"]=="mem20agentoutputcompilerz"
def test_eco_presence(): r=_eco().team_presence(); assert r["ok"] and r["subsystem"]=="mem20realtimeteampresencez"
def test_eco_episodic(): r=_eco().episodic_memory(); assert r["ok"] and r["subsystem"]=="mem20episodicmemorygraphz"
def test_eco_events(): r=_eco().blackboard_events("b",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().blackboard_routing("k",["b"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.blackboard_report(); assert rep["health"]["items"]==1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
