import importlib
MOD="mem20runtimecompatibilityenginez"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_python(): assert _m().check_python((3,1)) is True
def test_deps(): assert _m().check_deps(["a"],["a"])["ok"] is True
def test_report(): r=_m().compatibility_report({"installed":[]},{"deps":[]}); assert "compatible" in r
def test_fixes(): f=_m().suggest_fixes({"python_ok":False,"deps":{"missing":["x"]}}); assert "upgrade python" in f
def test_eco_config(): r=_eco().config_compat({"p":"3"}); assert r["ok"] and r["subsystem"]=="mem20deterministicconfigurationgraphz"
def test_eco_route(): r=_eco().capability_routing("k",["c"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_events(): r=_eco().compat_events("c",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_contain(): r=_eco().check_containment("c"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_heal(): r=_eco().healing_fixes(["f"]); assert r["ok"] and r["subsystem"]=="mem20selfhealingplansz"
def test_eco_device(): r=_eco().device_runtime({"cpu":True}); assert r["ok"] and r["subsystem"]=="mem20devicecapabilitycompilerz"
def test_report_and_probe():
    m=_m(); rep=m.runtime_report(); assert rep["compatible"] is True and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
