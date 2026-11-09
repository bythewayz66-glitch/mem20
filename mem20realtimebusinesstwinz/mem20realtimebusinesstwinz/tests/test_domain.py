import importlib
MOD="mem20realtimebusinesstwinz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_create(): assert _m().create_twin("x")["business"]=="x"
def test_kpi(): t=_m().create_twin("x"); _m().update_kpi(t,"r",10); assert t["kpis"]["r"]==10
def test_alerts(): t=_m().create_twin("x"); _m().update_kpi(t,"c",0.2); a=_m().check_alerts(t,{"c":0.1}); assert len(a)==1
def test_scenario(): t=_m().create_twin("x"); _m().update_kpi(t,"r",10); s=_m().scenario(t,{"r":15}); assert s["delta"]["r"]==5
def test_health(): t=_m().create_twin("x"); assert _m().twin_health(t)["fresh"] is True
def test_eco_biz(): r=_eco().business_scenarios(100); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_forecast(): r=_eco().kpi_forecast([10,12]); assert r["ok"] and r["subsystem"]=="mem20demandforecastandcapacitybrainz"
def test_eco_events(): r=_eco().kpi_events("k",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_health(): r=_eco().health_alerts(["k"]); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_eco_cf(): r=_eco().counterfactual_scenarios({"r":100}); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_route(): r=_eco().capability_routing("k",["t"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.business_twin_report(); assert rep["alerts"]>=1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
