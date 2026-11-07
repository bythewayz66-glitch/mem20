import importlib
MOD="mem20selfhealingplansz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_create(): p=_m().create_plan(["a"]); assert p["steps"][0]["status"]=="pending"
def test_execute(): p=_m().create_plan(["a"]); _m().execute_step(p,0,lambda n: None); assert p["steps"][0]["status"]=="done"
def test_heal_retry():
    p=_m().create_plan(["a"]); c={"n":0}
    def flaky(n):
        c["n"]+=1
        if c["n"]==1: raise RuntimeError("x")
    _m().execute_step(p,0,flaky); assert p["steps"][0]["status"]=="healed"
def test_status(): p=_m().create_plan(["a"]); _m().execute_step(p,0,lambda n: None); assert _m().plan_status(p)["done"]==1
def test_heal_plan(): p={"steps":[{"status":"failed"}]}; _m().heal_plan(p); assert p["steps"][0]["status"]=="pending"
def test_eco_contain(): r=_eco().step_containment("s"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_events(): r=_eco().healing_events("h",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().plan_routing("k",["h"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_health(): r=_eco().health_triggers(["p"]); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_eco_causal(): r=_eco().causal_repair({"f":1},{"f":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_recovery(): r=_eco().recovery_director(); assert r["ok"] and r["subsystem"]=="mem20autonomousrecoverydirectorz"
def test_report_and_probe():
    m=_m(); rep=m.healing_report(); assert rep["done"]>=1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
