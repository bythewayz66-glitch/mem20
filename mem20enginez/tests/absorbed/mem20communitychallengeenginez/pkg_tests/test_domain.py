import importlib
MOD="mem20communitychallengeenginez"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_challenge():
    m=_m(); c=m.create_challenge("w",10); m.join(c,"u1"); m.record_progress(c,"u1",10); assert m.check_completion(c)["completed"]
def test_leaderboard():
    m=_m(); c=m.create_challenge("w",10); m.join(c,"a"); m.join(c,"b"); m.record_progress(c,"a",5); m.record_progress(c,"b",3)
    assert m.leaderboard(c)[0]["user"]=="a"
def test_rewards(): m=_m(); c=m.create_challenge("w",10); m.join(c,"a"); m.record_progress(c,"a",10); assert "a" in m.reward_pool(c,100)
def test_ecosystem_quest_rewards(): r=_eco().quest_rewards(10); assert r["ok"] and r["subsystem"]=="mem20dynamicquestrewardcomposerz"
def test_ecosystem_events(): r=_eco().challenge_events("e",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_ecosystem_loyalty(): r=_eco().loyalty_signal(["community"]); assert r["ok"] and r["subsystem"]=="mem20crossproductloyaltygraphz"
def test_ecosystem_engagement(): r=_eco().engagement_signal(3); assert r["ok"] and r["subsystem"]=="mem20autonomoussaleslaboratoryz"
def test_ecosystem_routing(): r=_eco().reward_routing("p",["r"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_ecosystem_lifecycle(): r=_eco().lifecycle_signal(); assert r["ok"] and r["subsystem"]=="mem20customerlifecycleenginez"
def test_report_and_probe():
    m=_m(); rep=m.challenge_report(); assert len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
