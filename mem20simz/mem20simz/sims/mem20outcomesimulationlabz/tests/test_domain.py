import importlib
MOD="mem20simz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_sim(): m=_m(); r=m.simulate_once({"base":100,"std":5},seed=1); assert isinstance(r,float)
def test_mc(): m=_m(); r=m.monte_carlo({"base":100,"std":5},n=10,seed=1); assert len(r)==10
def test_sum(): m=_m(); r=m.summarize([1.0,2.0,3.0]); assert "mean" in r
def test_compare(): m=_m(); r=m.scenario_compare([{"name":"a","params":{"base":100,"std":5},"seed":1}]); assert r[0]["name"]=="a"
def test_risk(): m=_m(); r=m.risk_of_loss([5, -1, 3],0); assert 0<=r<=1

def test_estate_context_real_integrations(tmp_path):
    m=_m(); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True

def test_eco_cf(): r=_eco().counterfactual(); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_twin(): r=_eco().business_twin(); assert r["ok"] and r["subsystem"]=="mem20realtimebusinesstwinz"
def test_eco_model(): r=_eco().business_model(); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_events(): r=_eco().sim_events("s",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().sim_routing("k",["s"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_causal(): r=_eco().causal_routing({"x":1},{"x":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_report_and_probe():
    m=_m(); rep=m.simulation_report(); assert rep["runs"]==20 and "mean" in rep["summary"] and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
