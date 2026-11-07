import importlib
MOD="mem20selftuningresourcegovernorz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_govern_throttle(): a=_m().govern({"c":100},{"c":90},{"c":0.8}); assert a and a[0]["action"]=="throttle"
def test_govern_release(): a=_m().govern({"c":100},{"c":10},{"c":0.8}); assert a and a[0]["action"]=="release"
def test_adjust_up(): assert _m().adjust_quota("c",100,0.9)==120.0
def test_adjust_down(): assert _m().adjust_quota("c",100,0.2)==80.0
def test_health(): h=_m().governor_health({"c":100},{"c":90}); assert h["overloaded"]==1
def test_eco_forecast(): r=_eco().demand_forecast([1,2]); assert r["ok"] and r["subsystem"]=="mem20demandforecastandcapacitybrainz"
def test_eco_causal(): r=_eco().causal_tuning({"u":1},{"u":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_contain(): r=_eco().tuning_containment("g"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_events(): r=_eco().governor_events("g",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().capacity_routing("k",["c"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_recovery(): r=_eco().recovery_director(); assert r["ok"] and r["subsystem"]=="mem20autonomousrecoverydirectorz"
def test_report_and_probe():
    m=_m(); rep=m.governor_report(); assert rep["actions"] and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
