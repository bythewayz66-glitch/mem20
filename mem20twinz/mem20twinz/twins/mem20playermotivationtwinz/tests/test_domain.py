import importlib
MOD="mem20twinz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_create(): t=_m().create_twin("p"); assert t["player"]=="p" and t["motivation"]==0.5
def test_update(): t=_m().create_twin("p"); _m().update(t,{"delta":0.3}); assert abs(t["motivation"]-0.8)<1e-9
def test_churn(): assert _m().predict_churn({"motivation":0.1}) is True
def test_segments(): assert _m().motivation_segments({"motivation":0.8})=="high"
def test_health(): h=_m().twin_health({"motivation":0.5,"history":[1,2]}); assert h["events"]==2
def test_eco_lifecycle(): r=_eco().lifecycle_context(); assert r["ok"] and r["subsystem"]=="mem20customerlifecycleenginez"
def test_eco_quest(): r=_eco().quest_motivation(); assert r["ok"] and r["subsystem"]=="mem20dynamicquestrewardcomposerz"
def test_eco_challenge(): r=_eco().challenge_engagement(); assert r["ok"] and r["subsystem"]=="mem20communitychallengeenginez"
def test_eco_cf(): r=_eco().motivation_scenarios(0.5); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_events(): r=_eco().motivation_events("m",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().capability_routing("k",["m"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.motivation_report(); assert 0<=rep["motivation"]<=1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
