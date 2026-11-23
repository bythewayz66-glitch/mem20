import importlib
MOD="mem20spatialcommanduniversez"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_region(): m=_m(); r=m.create_region("r1",[(0,10),(0,10)]); assert r["name"]=="r1"
def test_add(): m=_m(); r=m.create_region("r1",[(0,10),(0,10)]); m.add_entity(r,"e1",(5,5)); assert len(r["entities"])==1
def test_dist(): m=_m(); assert m.distance((0,0),(3,4))==5.0
def test_in(): m=_m(); r=m.create_region("r1",[(0,10),(0,10)]); assert m.in_region(r,(5,5)) is True
def test_health(): m=_m(); r=m.create_region("r1",[(0,10),(0,10)]); assert m.spatial_health([r])["regions"]==1
def test_estate_context_real_integrations(tmp_path):
    m=importlib.import_module("mem20spatialcommanduniversez.domain"); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True
def test_eco_workcell(): r=_eco().workcell_dispatch(); assert r["ok"] and r["subsystem"]=="mem20autonomousworkcellsz"
def test_eco_causal(): r=_eco().causal_routing({"d":1},{"d":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_events(): r=_eco().spatial_events("s",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().spatial_routing("k",["s"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_contain(): r=_eco().spatial_containment("s"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_health_peer(): r=_eco().spatial_health_peer(); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_report_and_probe():
    m=_m(); rep=m.spatial_report(); assert rep["health"]["entities"]==1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
