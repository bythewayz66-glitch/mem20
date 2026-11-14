import importlib
MOD="mem20dynamicskillgraphz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_add(): g={}; _m().add_skill(g,"a"); assert "a" in g["skills"]
def test_prof(): g={}; _m().add_skill(g,"a"); _m().update_proficiency(g,"a",0.5); assert g["skills"]["a"]["proficiency"]==0.5
def test_path(): g={}; _m().add_skill(g,"a"); _m().add_skill(g,"b",["a"]); assert _m().learning_path(g,"b")==["a","b"]
def test_gap(): g={}; _m().add_skill(g,"a"); g["skills"]["a"]["proficiency"]=0.2; assert _m().skill_gap(g,["a"])[0]["gap"]==0.8
def test_stats(): g={}; _m().add_skill(g,"a"); _m().update_proficiency(g,"a",1.0); assert _m().graph_stats(g)["count"]==1
def test_eco_match(): r=_eco().capability_match("k",["s"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_quest(): r=_eco().quest_progression(); assert r["ok"] and r["subsystem"]=="mem20dynamicquestrewardcomposerz"
def test_eco_lifecycle(): r=_eco().lifecycle_progression(); assert r["ok"] and r["subsystem"]=="mem20customerlifecycleenginez"
def test_eco_events(): r=_eco().skill_events("e",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_causal(): r=_eco().causal_routing({"g":1},{"g":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_compress(): r=_eco().context_compression("skills path"); assert r["ok"] and r["subsystem"]=="mem20rewardforgez"
def test_report_and_probe():
    m=_m(); rep=m.skill_report(); assert len(rep["path"])>0 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
