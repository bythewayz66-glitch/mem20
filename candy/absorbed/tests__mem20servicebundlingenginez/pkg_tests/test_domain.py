import importlib
MOD="mem20servicebundlingenginez"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_create(): m=_m(); r=m.create_bundle([{"price":5},{"price":3}]); assert r["price"]==8
def test_add(): m=_m(); r=m.create_bundle([]); m.add_service(r,{"price":4}); assert r["price"]==4
def test_disc(): m=_m(); r=m.create_bundle([{"price":10}]); m.discount(r,0.1); assert r["price"]==9.0
def test_health(): m=_m(); r=m.bundle_health([m.create_bundle([])]); assert r["bundles"]==1
def test_estate_context_real_integrations(tmp_path):
    m=importlib.import_module("mem20servicebundlingenginez.domain"); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True
def test_eco_deal(): r=_eco().deal_pricing(10); assert r["ok"] and r["subsystem"]=="mem20autonomousdealdeskz"
def test_eco_plg(): r=_eco().plg_sim(); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_market(): r=_eco().bundle_market("k",["b"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_events(): r=_eco().bundle_events("b",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_health_peer(): r=_eco().bundle_health_peer(); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_eco_revenue(): r=_eco().revenue_check(10); assert r["ok"] and r["subsystem"]=="mem20revenueleakhunterz"
def test_report_and_probe():
    m=_m(); rep=m.bundle_report(); assert rep["health"]["bundles"]==1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
