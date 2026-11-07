import importlib
MOD="mem20skillbasedprogressionbrainz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_xp(): m=_m(); r=m.gain_xp({"xp":0},100); assert r["xp"]==100
def test_unlock(): m=_m(); r=m.gain_xp({"xp":0,"skills":[]},50); res=m.unlock_skill(r,"s1",30); assert res["ok"] is True
def test_level(): m=_m(); r=m.gain_xp({"xp":0,"level":1},100); assert m.level(r)>=1
def test_health(): m=_m(); r=m.gain_xp({"xp":0},10); assert "level" in m.progression_health(r)
def test_estate_context_real_integrations(tmp_path):
    m=importlib.import_module("mem20skillbasedprogressionbrainz.domain"); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True
def test_eco_graph(): r=_eco().skill_graph(); assert r["ok"] and r["subsystem"]=="mem20dynamicskillgraphz"
def test_eco_motivation(): r=_eco().motivation_twin(); assert r["ok"] and r["subsystem"]=="mem20playermotivationtwinz"
def test_eco_reward(): r=_eco().reward_forge(); assert r["ok"] and r["subsystem"]=="mem20rewardforgez"
def test_eco_events(): r=_eco().progression_events("p",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().progression_routing("k",["p"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_health_peer(): r=_eco().progression_health_peer(); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_report_and_probe():
    m=_m(); rep=m.progression_report(); assert rep["health"]["level"]>=2 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
