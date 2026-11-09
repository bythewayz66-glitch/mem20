import importlib
MOD="mem20customerlifecycleenginez"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_stage(): assert _m().lifecycle_stage({"days_since_signup":3,"purchases":0})=="onboarding"
def test_transition(): assert _m().transition({"days_since_signup":30,"purchases":1},"purchase")=="active"
def test_retention(): assert 0<=_m().retention_probability({"engagement":0.5,"recency_days":30})<=1
def test_ltv(): assert _m().lifetime_value({"avg_order_value":50,"purchase_frequency":2,"expected_lifespan_months":12})==1200.0
def test_segments(): s=_m().segment_customers([{"id":"a","days_since_signup":3,"purchases":0}]); assert "a" in s["onboarding"]
def test_eco_biz(): r=_eco().business_value(100); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_pipeline(): r=_eco().pipeline_signal(100); assert r["ok"] and r["subsystem"]=="mem20autonomoussaleslaboratoryz"
def test_eco_loyalty(): r=_eco().loyalty_context(["core"]); assert r["ok"] and r["subsystem"]=="mem20crossproductloyaltygraphz"
def test_eco_demand(): r=_eco().demand_signal([10,12]); assert r["ok"] and r["subsystem"]=="mem20demandforecastandcapacitybrainz"
def test_eco_events(): r=_eco().lifecycle_events("e",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_growth(): r=_eco().growth_partnerships(); assert r["ok"] and r["subsystem"]=="mem20acquisitionandpartnershipscoutz"
def test_report_and_probe():
    m=_m(); rep=m.lifecycle_report(); assert rep["ltv"]>0 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
