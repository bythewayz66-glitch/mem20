import importlib
MOD="mem20offerassemblyfabricz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_create(): m=_m(); r=m.create_offer([{"price":5}],10); assert r["status"]=="draft"
def test_add(): m=_m(); r=m.create_offer([],0); m.add_component(r,{"price":3}); assert len(r["components"])==1
def test_price(): m=_m(); r=m.create_offer([{"price":5},{"price":3}],0); assert m.price_offer(r,"sum")==8
def test_publish(): m=_m(); r=m.create_offer([],0); m.publish(r); assert r["status"]=="published"
def test_health(): m=_m(); r=m.offer_health([m.create_offer([],0)]); assert r["total"]==1

def test_estate_context_real_integrations(tmp_path):
    m=_m(); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True

def test_eco_deal(): r=_eco().deal_desk(); assert r["ok"] and r["subsystem"]=="mem20autonomousdealdeskz"
def test_eco_bundle(): r=_eco().bundle_engine(); assert r["ok"] and r["subsystem"]=="mem20servicebundlingenginez"
def test_eco_plg(): r=_eco().plg_sim(); assert r["ok"] and r["subsystem"]=="mem20productledgrowthsimulatorz"
def test_eco_revenue(): r=_eco().revenue_check(); assert r["ok"] and r["subsystem"]=="mem20revenueleakhunterz"
def test_eco_events(): r=_eco().offer_events("o",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().offer_routing("k",["o"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.offer_report(); assert rep["price"]==8 and rep["health"]["published"]==1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
