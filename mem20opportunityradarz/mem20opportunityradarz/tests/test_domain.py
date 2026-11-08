import importlib
MOD="mem20opportunityradarz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_scan(): m=_m(); r=m.scan([{"score":0.3},{"score":0.8}],0.5); assert len(r)==1
def test_score(): m=_m(); r=m.score_opportunity({"value":10,"probability":0.5},{"urgency":2}); assert r==10.0
def test_rank(): m=_m(); r=m.rank([{"value":5,"probability":0.5},{"value":10,"probability":0.5}],{}); assert r[0]["value"]==10
def test_alert(): m=_m(); r=m.alert([{"score":0.8},{"score":0.4}],0.7); assert len(r)==1
def test_health(): m=_m(); r=m.radar_health([{"score":0.8}]); assert r["high"]==1

def test_estate_context_real_integrations(tmp_path):
    m=_m(); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True

def test_eco_sales(): r=_eco().sales_lab(); assert r["ok"] and r["subsystem"]=="mem20autonomoussaleslaboratoryz"
def test_eco_plg(): r=_eco().plg_sim(); assert r["ok"] and r["subsystem"]=="mem20productledgrowthsimulatorz"
def test_eco_causal(): r=_eco().causal_routing({"x":1},{"x":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_revenue(): r=_eco().revenue_check(); assert r["ok"] and r["subsystem"]=="mem20revenueleakhunterz"
def test_eco_events(): r=_eco().radar_events("r",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().radar_routing("k",["r"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.radar_report(); assert rep["scanned"]==1 and rep["health"]["high"]==1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
