import importlib
MOD="mem20planetarybatchfabricz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_submit(): m=_m(); r=m.submit_job("us","p",1); assert r["status"]=="queued"
def test_sched(): m=_m(); j=m.submit_job("us","p",1); r=m.schedule([j],{"us":1}); assert len(r)==1
def test_status(): m=_m(); j=m.submit_job("us","p",1); assert m.job_status(j)=="queued"
def test_health(): m=_m(); r=m.fabric_health({"us":5,"eu":3}); assert r["regions"]==2
def test_retry(): m=_m(); j=m.submit_job("us","p",1); r=m.retry(j); assert r["ok"] is True

def test_estate_context_real_integrations(tmp_path):
    m=_m(); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True

def test_eco_scheduler(): r=_eco().roaming_scheduler(); assert r["ok"] and r["subsystem"]=="mem20roamingworkloadschedulerz"
def test_eco_workcell(): r=_eco().workcell_run(); assert r["ok"] and r["subsystem"]=="mem20autonomousworkcellsz"
def test_eco_events(): r=_eco().batch_events("b",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().batch_routing("k",["b"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_recovery(): r=_eco().autonomous_recovery(); assert r["ok"] and r["subsystem"]=="mem20autonomousrecoverydirectorz"
def test_eco_compile(): r=_eco().output_compile(); assert r["ok"] and r["subsystem"]=="mem20agentoutputcompilerz"
def test_report_and_probe():
    m=_m(); rep=m.fabric_report(); assert rep["scheduled"]==1 and rep["health"]["regions"]==2 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
