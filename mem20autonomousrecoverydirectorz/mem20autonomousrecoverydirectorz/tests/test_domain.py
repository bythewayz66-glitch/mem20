import importlib
MOD="mem20autonomousrecoverydirectorz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_triage(): assert _m().triage({"severity":"critical"})["priority"]==1
def test_rollback(): assert "steps" in _m().rollback_plan({"version":2},{"version":1})
def test_remediate(): assert len(_m().remediate({},[{"safe":True},{"safe":False}])["applied"])==1
def test_time(): assert _m().recovery_time({"severity":"low"})==60
def test_health(): assert 0<=_m().health_after({"success_rate":0.8})<=1
def test_ecosystem_fault_containment(): r=_eco().fault_containment("api"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_ecosystem_healing_plan(): r=_eco().healing_plan(["diagnose"]); assert r["ok"] and r["subsystem"]=="mem20selfhealingplansz"
def test_ecosystem_health_signal(): r=_eco().health_signal(["api"]); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz" and "overall" in r
def test_ecosystem_recovery_pipeline(): r=_eco().recovery_pipeline("asset"); assert r["ok"] and r["subsystem"]=="mem20pipez"
def test_ecosystem_incident_events(): r=_eco().incident_events({"severity":"high"}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz" and r["published"]==1
def test_ecosystem_swarm_status(): r=_eco().swarm_status("n1"); assert r["ok"] and r["subsystem"]=="mem20zerotouchnodeswarmz"
def test_recovery_report_and_probe():
    m=_m(); rep=m.recovery_report(); assert rep["triage"]["priority"]>=1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
