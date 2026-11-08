import importlib
MOD="mem20personalmodelevolutionz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_create(): m=_m(); r=m.create_model("u1"); assert r["user"]=="u1"
def test_adapt(): m=_m(); r=m.create_model("u1"); m.adapt(r,{"x":1.0}); assert r["version"]==2
def test_predict(): m=_m(); r=m.create_model("u1"); m.adapt(r,{"x":1.0}); assert isinstance(m.predict(r,{"x":1}),float)
def test_reset(): m=_m(); r=m.create_model("u1"); m.adapt(r,{"x":1.0}); m.reset(r); assert r["version"]==1
def test_health(): m=_m(); r=m.create_model("u1"); assert "version" in m.evolution_health(r)

def test_estate_context_real_integrations(tmp_path):
    m=_m(); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True

def test_eco_collective(): r=_eco().collective_intel(); assert r["ok"] and r["subsystem"]=="mem20collectivemodelintelligencez"
def test_eco_transfer(): r=_eco().skill_transfer(); assert r["ok"] and r["subsystem"]=="mem20skillmemorytransferz"
def test_eco_episodic(): r=_eco().episodic_memory(); assert r["ok"] and r["subsystem"]=="mem20episodicmemorygraphz"
def test_eco_events(): r=_eco().evo_events("e",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().evo_routing("k",["e"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_causal(): r=_eco().causal_routing({"x":1},{"x":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_report_and_probe():
    m=_m(); rep=m.evolution_report(); assert rep["health"]["version"]==2 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
