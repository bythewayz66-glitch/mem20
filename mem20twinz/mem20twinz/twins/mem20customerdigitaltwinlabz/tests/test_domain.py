import importlib
MOD="mem20twinz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_build(): assert _m().build_twin({"id":"x"})["id"]=="x"
def test_sim(): assert len(_m().simulate_behavior({"behavior":{"engagement":1}},{"steps":3,"seed":0}))==3
def test_churn(): assert 0<=_m().predict_churn({"behavior":{"engagement":0.5,"recency_days":30}})<=1
def test_action(): assert _m().recommend_action({"ltv":2000,"behavior":{"engagement":0.9,"recency_days":1}})=="upsell"
def test_accuracy(): assert 0<=_m().twin_accuracy({"behavior":{"engagement":0.5}},{"churned":False})<=1
def test_eco_lifecycle(): r=_eco().lifecycle_signal({"tenure_months":1,"spend":10}); assert r["ok"] and r["subsystem"]=="mem20customerlifecycleenginez"
def test_eco_cf(): r=_eco().counterfactual_scenarios({"engagement":0.5}); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_demand(): r=_eco().demand_signal([1,2,3]); assert r["ok"] and r["subsystem"]=="mem20demandforecastandcapacitybrainz"
def test_eco_loyalty(): r=_eco().loyalty_context(["core"]); assert r["ok"] and r["subsystem"]=="mem20crossproductloyaltygraphz"
def test_eco_events(): r=_eco().twin_events("e",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().capability_routing("k",["p"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.twin_report(); assert rep["recommended_action"] in ("retention_offer","upsell","nurture") and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
