import importlib
MOD="mem20realworldimpactrewardsz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_record(): i={}; _m().record_impact(i,"u","t",1); assert len(i["u"])==1
def test_reward(): i={"u":[{"magnitude":2},{"magnitude":1}]}; assert _m().compute_reward(i,"u")==3.0
def test_leaderboard(): i={"a":[{"magnitude":1}],"b":[{"magnitude":3}]}; assert _m().leaderboard(i)[0]["user"]=="b"
def test_health(): assert _m().impact_health({"u":[{},{}]})["events"]==2
def test_eco_quest(): r=_eco().quest_rewards(1.0); assert r["ok"] and r["subsystem"]=="mem20dynamicquestrewardcomposerz"
def test_eco_loyalty(): r=_eco().loyalty_impact("u",1.0); assert r["ok"] and r["subsystem"]=="mem20crossproductloyaltygraphz"
def test_eco_lifecycle(): r=_eco().lifecycle_value(); assert r["ok"] and r["subsystem"]=="mem20customerlifecycleenginez"
def test_eco_events(): r=_eco().impact_events("i",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().reward_routing("k",["r"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_forecast(): r=_eco().impact_forecast([1,2]); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_report_and_probe():
    m=_m(); rep=m.impact_report(); assert rep["leaderboard"][0]["user"]=="alice" and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
