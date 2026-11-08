import importlib
MOD="mem20syntheticevaluatorarenaz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_create(): m=_m(); r=m.create_arena(["a","b"]); assert len(r["agents"])==2
def test_eval(): m=_m(); r=m.create_arena(["a","b"]); m.evaluate(r,"a","b",0.9); assert len(r["evaluations"])==1
def test_lb(): m=_m(); r=m.create_arena(["a","b"]); m.evaluate(r,"a","b",0.9); lb=m.leaderboard(r); assert lb[0]["agent"]=="b"
def test_health(): m=_m(); r=m.create_arena(["a","b"]); assert m.arena_health(r)["agents"]==2
def test_estate_context_real_integrations(tmp_path):
    m=importlib.import_module("mem20syntheticevaluatorarenaz.domain"); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True
def test_eco_collective(): r=_eco().collective_intel(); assert r["ok"] and r["subsystem"]=="mem20collectivemodelintelligencez"
def test_eco_cf(): r=_eco().counterfactual_eval(); assert r["ok"] and r["subsystem"]=="mem20counterfactualmemorysimulatorz"
def test_eco_compile(): r=_eco().output_compile(); assert r["ok"] and r["subsystem"]=="mem20agentoutputcompilerz"
def test_eco_events(): r=_eco().arena_events("a",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().arena_routing("k",["a"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_contain(): r=_eco().arena_containment("a"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_report_and_probe():
    m=_m(); rep=m.arena_report(); assert rep["health"]["evaluations"]==1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
