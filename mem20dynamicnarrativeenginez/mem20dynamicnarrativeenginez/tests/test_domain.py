import importlib
MOD="mem20dynamicnarrativeenginez"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_story(): s=_m().create_story("a"); _m().add_node(s,"a","hi",[{"label":"x","target":"b"}]); _m().add_node(s,"b","bye"); _m().choose(s,0); assert s["current"]=="b"
def test_text(): s=_m().create_story("a"); _m().add_node(s,"a","hello"); assert _m().current_text(s)=="hello"
def test_choices(): s=_m().create_story("a"); _m().add_node(s,"a","", [{"label":"x","target":"a"}]); assert len(_m().available_choices(s))==1
def test_state(): s=_m().create_story("a"); st=_m().narrative_state(s); assert st["total_nodes"]==1
def test_eco_events(): r=_eco().narrative_events("x",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_challenge(): r=_eco().challenge_hooks(); assert r["ok"] and r["subsystem"]=="mem20communitychallengeenginez"
def test_eco_compress(): r=_eco().context_compression("hello world story text"); assert r["ok"] and r["subsystem"]=="mem20rewardforgez"
def test_eco_focus(): r=_eco().focus_guidance({"goal":"x","priority":1}); assert r["ok"] and r["subsystem"]=="mem20mixedinitiativefocusenginez"
def test_eco_route(): r=_eco().capability_routing("k",["s"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_branch(): r=_eco().branching_scenarios({"c":1}); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_report_and_probe():
    m=_m(); rep=m.narrative_report(); assert rep["state"]["current"] and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
