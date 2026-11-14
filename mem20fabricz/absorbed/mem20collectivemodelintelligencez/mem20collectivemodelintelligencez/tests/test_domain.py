import importlib
MOD="mem20collectivemodelintelligencez"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_ens_num(): assert _m().ensemble_predict([1,2,3])==2.0
def test_ens_vote(): assert _m().ensemble_predict(["a","a","b"])=="a"
def test_div(): assert 0<=_m().diversity_score([1,1,2])<=1
def test_distill(): assert _m().knowledge_distill([1,0],[0.9,0.1])>=0
def test_conf(): assert _m().aggregate_confidence([0.8,0.6])==0.7
def test_ecosystem_fusion(): r=_eco().model_fusion([]); assert r["ok"] and r["subsystem"]=="mem20livemodelfusionz"
def test_ecosystem_quality(): r=_eco().generation_quality("x"); assert r["ok"] and r["subsystem"]=="mem20loreragcontentgeneratorz"
def test_ecosystem_routing(): r=_eco().model_routing("k",["m"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_ecosystem_events(): r=_eco().ensemble_events("e",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_ecosystem_health(): r=_eco().model_health(["a"]); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_ecosystem_causal(): r=_eco().causal_route({"q":1},{"q":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_report_and_probe():
    m=_m(); rep=m.collective_report(); assert rep["ensemble"] is not None and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
