import importlib,time
MOD="mem20realtimeteampresencez"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_set_get(): p={}; _m().set_presence(p,"u","online"); assert _m().get_presence(p,"u")["status"]=="online"
def test_online(): p={}; _m().set_presence(p,"a","online"); _m().set_presence(p,"b","offline"); assert _m().online_users(p)==["a"]
def test_away(): p={"users":{"u":{"status":"online","updated":time.time()-999}}}; assert "u" in _m().away_users(p,10)
def test_health(): p={}; _m().set_presence(p,"a","online"); assert _m().presence_health(p)["total"]==1
def test_eco_events(): r=_eco().presence_events("p",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().presence_routing("k",["p"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_health(): r=_eco().service_health(["p"]); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_eco_contain(): r=_eco().presence_containment("u"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_heal(): r=_eco().reconnect_plans(["r"]); assert r["ok"] and r["subsystem"]=="mem20selfhealingplansz"
def test_eco_focus(): r=_eco().focus_context({"priority":1}); assert r["ok"] and r["subsystem"]=="mem20mixedinitiativefocusenginez"
def test_report_and_probe():
    m=_m(); rep=m.presence_report(); assert rep["online"]==2 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
