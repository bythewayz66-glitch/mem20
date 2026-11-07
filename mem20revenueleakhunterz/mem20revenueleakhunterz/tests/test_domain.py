import importlib
MOD="mem20revenueleakhunterz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_detect(): leaks=_m().detect_leaks([{"id":"a","amount":5}], {"a":10}); assert leaks[0]["delta"]==-5
def test_anomaly(): assert _m().anomaly_score([1,1,1,10]) > 0
def test_recoverable(): assert _m().recoverable([{"delta":-5},{"delta":2}])==7.0
def test_health(): assert _m().hunter_health([{"delta":1}])["leaks"]==1
def test_eco_econ(): r=_eco().revenue_economics(100,60); assert r["ok"] and r["subsystem"]=="mem20businessmodelsimulatorz"
def test_eco_deal(): r=_eco().deal_pricing(50); assert r["ok"] and r["subsystem"]=="mem20autonomousdealdeskz"
def test_eco_events(): r=_eco().leak_events("l",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_contain(): r=_eco().leak_containment("l"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_causal(): r=_eco().causal_analysis({"d":1},{"d":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_route(): r=_eco().hunter_routing("k",["h"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.leak_report(); assert rep["leaks"]==2 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
