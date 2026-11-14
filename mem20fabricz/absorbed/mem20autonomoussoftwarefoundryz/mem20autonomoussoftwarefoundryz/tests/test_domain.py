import importlib
MOD="mem20autonomoussoftwarefoundryz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_spec(): assert len(_m().spec_to_tasks({"features":["auth","api"]}))>=3
def test_quality(): assert _m().code_quality({"tests_pass":True,"coverage":0.9,"lint_clean":True})==1.0
def test_deploy(): assert _m().deploy_decision(0.8) is True
def test_effort(): assert _m().estimate_effort({"features":["a","b","c"]})["days"]==6
def test_artifact(): assert "checksum" in _m().build_artifact({"name":"app"},"code")
def test_ecosystem_capability_routing(): r=_eco().capability_routing("b1",["lint"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_ecosystem_artifact_recovery(): r=_eco().artifact_recovery("app"); assert r["ok"] and r["subsystem"]=="mem20pipez"
def test_ecosystem_build_events(): r=_eco().build_events("x",{"a":1}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_ecosystem_deploy_containment(): r=_eco().deploy_containment("deploy"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_ecosystem_spec_quality(): r=_eco().spec_quality("build"); assert r["ok"] and r["subsystem"]=="mem20loreragcontentgeneratorz"
def test_ecosystem_effort_economics(): r=_eco().effort_economics(6); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_foundry_report_and_probe():
    m=_m(); rep=m.foundry_report(); assert rep["quality"]==1.0 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
