import importlib
MOD="mem20uniteconomicsautopilotz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_ltv(): m=_m(); r=m.ltv(10,0.1); assert r==100.0
def test_cac(): m=_m(); r=m.cac(100,5); assert r==20.0
def test_pay(): m=_m(); r=m.payback_months(20,10); assert r==2.0
def test_ratio(): m=_m(); r=m.ltv_cac_ratio(100,20); assert r==5.0
def test_health(): m=_m(); r=m.economics_health({"ltv":100,"cac":20,"ratio":5}); assert "ratio" in r
def test_estate_context_real_integrations(tmp_path):
    m=importlib.import_module("mem20uniteconomicsautopilotz.domain"); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True
def test_eco_revenue(): r=_eco().revenue_check(); assert r["ok"] and r["subsystem"]=="mem20revenueleakhunterz"
def test_eco_plg(): r=_eco().plg_sim(); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_model(): r=_eco().business_model(); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_events(): r=_eco().economics_events("e",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().economics_routing("k",["e"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_health_peer(): r=_eco().economics_health_peer(); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_report_and_probe():
    m=_m(); rep=m.economics_report(); assert rep["ratio"]==5.0 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
