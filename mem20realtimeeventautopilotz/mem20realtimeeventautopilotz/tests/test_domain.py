import importlib
MOD="mem20realtimeeventautopilotz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_ingest(): s={}; _m().ingest_event(s,{"x":1}); assert len(s["events"])==1
def test_rules(): acts=_m().evaluate_rules({"v":2}, [{"condition":lambda e:e["v"]>1,"action":"a"}]); assert acts==["a"]
def test_autopilot(): s={"events":[{"v":2}]}; r=_m().autopilot(s,[{"condition":lambda e:e["v"]>1,"action":"a"}]); assert r[0]["actions"]==["a"]
def test_throttle(): s={"events":list(range(20))}; _m().throttle(s,5); assert len(s["events"])==5
def test_health(): assert _m().autopilot_health({"events":[1,2]})["events"]==2
def test_eco_stream(): r=_eco().stream_backbone("e",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_contain(): r=_eco().action_containment("n"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_heal(): r=_eco().healing_actions(["r"]); assert r["ok"] and r["subsystem"]=="mem20selfhealingplansz"
def test_eco_causal(): r=_eco().causal_decisions({"s":1},{"s":1}); assert r["ok"] and r["subsystem"]=="mem20causalroutingbrainz"
def test_eco_health(): r=_eco().health_triggers(["s"]); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_eco_route(): r=_eco().capability_routing("k",["a"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_report_and_probe():
    m=_m(); rep=m.autopilot_report(); assert rep["actions_triggered"]>=1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
