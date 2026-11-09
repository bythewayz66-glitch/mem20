import importlib
MOD="mem20rewardforgez"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_linear(): assert _m().linear_reward({"a":2},{"a":3})==6
def test_shaped(): assert _m().shaped_reward(1,0.5)==1.5
def test_normalize(): assert _m().normalize([0,10])==[0.0,1.0]
def test_health(): assert _m().reward_health([1,3])["mean"]==2.0
def test_eco_quest(): r=_eco().quest_reward_shapes(); assert r["ok"] and r["subsystem"]=="mem20dynamicquestrewardcomposerz"
def test_eco_impact(): r=_eco().impact_rewards(); assert r["ok"] and r["subsystem"]=="mem20realworldimpactrewardsz"
def test_eco_cf(): r=_eco().counterfactual_shaping({"r":1}); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_events(): r=_eco().reward_events("r",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().reward_routing("k",["r"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_causal(): r=_eco().causal_weighting({"r":1},{"r":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_report_and_probe():
    m=_m(); rep=m.forge_report(); assert rep["shaped"]==3.0 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
