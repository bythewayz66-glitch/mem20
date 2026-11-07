import importlib
MOD="mem20runtimepromptoptimizerz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_tokenize(): assert _m().tokenize("a b")==["a","b"]
def test_compress(): assert _m().compress("a b c",2).endswith("...")
def test_score(): assert _m().score_prompt("hello world",{"hello":1})==1.0
def test_optimize(): o=_m().optimize("hello world",{"hello":1},10); assert o["score"]==1.0
def test_health(): assert _m().prompt_health(["a b"])["avg_tokens"]==2.0
def test_eco_compress(): r=_eco().context_compression("text"); assert r["ok"] and r["subsystem"]=="mem20contextcompressionforgez"
def test_eco_causal(): r=_eco().causal_routing({"q":1},{"q":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_route(): r=_eco().capability_routing("k",["o"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_events(): r=_eco().prompt_events("p",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_contain(): r=_eco().optimize_containment("p"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_forecast(): r=_eco().cost_forecast([10,9]); assert r["ok"] and r["subsystem"]=="mem20demandforecastandcapacitybrainz"
def test_report_and_probe():
    m=_m(); rep=m.prompt_report(); assert rep["score"]>0 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
