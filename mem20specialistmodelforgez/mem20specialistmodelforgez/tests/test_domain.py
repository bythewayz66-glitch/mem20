import importlib
MOD="mem20specialistmodelforgez"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_forge(): m=_m(); r=m.forge("base","code",["d1"]); assert "code" in r["name"]
def test_eval(): m=_m(); r=m.forge("base","code",["d1"]); assert 0<=m.evaluate(r,["t"])<=1
def test_merge(): m=_m(); a=m.forge("base","code",["d1"]); b=m.forge("base","math",["d2"]); r=m.merge_specialists([a,b]); assert "merged" in r["name"]
def test_health(): m=_m(); r=m.forge("base","code",["d1"]); assert m.forge_health([r])["models"]==1
def test_estate_context_real_integrations(tmp_path):
    m=importlib.import_module("mem20specialistmodelforgez.domain"); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True
def test_eco_collective(): r=_eco().collective_intel(); assert r["ok"] and r["subsystem"]=="mem20collectivemodelintelligencez"
def test_eco_causal(): r=_eco().causal_routing({"q":1},{"q":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_events(): r=_eco().forge_events("f",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().forge_routing("k",["f"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_contain(): r=_eco().forge_containment("f"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_foundry(): r=_eco().software_foundry(); assert r["ok"] and r["subsystem"]=="mem20autonomoussoftwarefoundryz"
def test_report_and_probe():
    m=_m(); rep=m.forge_report(); assert rep["health"]["models"]==1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
