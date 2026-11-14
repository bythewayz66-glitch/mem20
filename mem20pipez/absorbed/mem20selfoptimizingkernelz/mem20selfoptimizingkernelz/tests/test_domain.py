import importlib
MOD="mem20selfoptimizingkernelz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_optimize(): n=_m().optimize({"a":0},{"a":10},0.5); assert n["a"]==5.0
def test_score(): assert _m().score({"a":2},{"a":3})==6
def test_search(): r=_m().search({"x":[1,2]},{"x":1},5,seed=0); assert r["score"] in (1,2)
def test_health(): assert _m().kernel_health({"a":1})["params"]==1
def test_eco_causal(): r=_eco().causal_tuning({"s":1},{"s":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_forecast(): r=_eco().demand_forecast([1,2]); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_cf(): r=_eco().counterfactual_eval({"score":1}); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_events(): r=_eco().tuning_events("t",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().kernel_routing("k",["o"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_contain(): r=_eco().tuning_containment("o"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_report_and_probe():
    m=_m(); rep=m.kernel_report(); assert rep["tuned_a"]==1.5 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
