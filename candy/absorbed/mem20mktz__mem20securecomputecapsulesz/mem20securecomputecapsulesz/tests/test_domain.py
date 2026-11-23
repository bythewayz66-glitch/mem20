import importlib
MOD="mem20securecomputecapsulesz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_create(): c=_m().create_capsule("x"); assert c["status"]=="created"
def test_run(): c=_m().create_capsule("2"); _m().run_capsule(c, lambda code,lim: int(code)); assert c["result"]==2
def test_run_fail(): c=_m().create_capsule("x"); _m().run_capsule(c, lambda c,l: (_ for _ in ()).throw(ValueError("x"))); assert c["status"]=="failed"
def test_isolate(): c=_m().create_capsule("x"); _m().isolate(c); assert c["isolated"] is True
def test_health(): h=_m().capsule_health([{"status":"completed"},{"status":"failed"}]); assert h["completed"]==1
def test_eco_contain(): r=_eco().capsule_containment("c"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_plans(): r=_eco().recovery_plans(["r"]); assert r["ok"] and r["subsystem"]=="mem20selfhealingplansz"
def test_eco_identity(): r=_eco().workload_identity("w"); assert r["ok"] and r["subsystem"]=="mem20secretslessworkloadidentityz"
def test_eco_route(): r=_eco().capsule_routing("k",["r"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_events(): r=_eco().capsule_events("c",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_config(): r=_eco().capsule_config({"c":1}); assert r["ok"] and r["subsystem"]=="mem20deterministicconfigurationgraphz"
def test_report_and_probe():
    m=_m(); rep=m.capsule_report(); assert rep["completed"]==1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
