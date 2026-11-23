import importlib
MOD="mem20universalhealthnervoussystemz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_reg(): m=_m(); r=m.register_subsystem({}, "s1", lambda: {"ok": True}); assert "s1" in r["subsystems"]
def test_check(): m=_m(); r=m.register_subsystem({}, "s1", lambda: {"ok": True}); m.check_all(r); assert r["subsystems"]["s1"]["status"]=="healthy"
def test_overall(): m=_m(); r=m.register_subsystem({}, "s1", lambda: {"ok": True}); m.check_all(r); assert m.overall(r)=="healthy"
def test_report(): m=_m(); r=m.register_subsystem({}, "s1", lambda: {"ok": True}); m.check_all(r); assert "overall" in m.health_report(r)

def test_estate_context_real_integrations(tmp_path):
    m = importlib.import_module("mem20universalhealthnervoussystemz.domain")
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

def test_eco_fault(): r=_eco().fault_containment("h"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_recovery(): r=_eco().recovery_director(); assert r["ok"] and r["subsystem"]=="mem20autonomousrecoverydirectorz"
def test_eco_heal(): r=_eco().self_healing(); assert r["ok"] and r["subsystem"]=="mem20selfhealingplansz"
def test_eco_events(): r=_eco().health_events("h",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().health_routing("k",["h"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_causal(): r=_eco().causal_routing({"x":1},{"x":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_nervous_report_and_probe():
    m=_m(); rep=m.nervous_report(); assert rep["health"]["overall"]=="healthy" and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
