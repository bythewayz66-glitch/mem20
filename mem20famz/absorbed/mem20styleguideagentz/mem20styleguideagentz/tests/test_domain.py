import importlib
MOD="mem20styleguideagentz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_check(): m=_m(); r=m.check("hello world", [{"type":"max_length","value":5}]); assert len(r)==1
def test_fix(): m=_m(); r=m.fix("hello",""); assert r=="hello"
def test_score(): m=_m(); r=m.style_score("hi", [{"type":"max_length","value":5}]); assert r==1.0
def test_health(): m=_m(); r=m.style_health("hi", [{"type":"max_length","value":5}]); assert r["score"]==1.0
def test_estate_context_real_integrations(tmp_path):
    m=importlib.import_module("mem20styleguideagentz.domain"); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True
def test_eco_compile(): r=_eco().output_compile(); assert r["ok"] and r["subsystem"]=="mem20agentoutputcompilerz"
def test_eco_foundry(): r=_eco().software_foundry(); assert r["ok"] and r["subsystem"]=="mem20autonomoussoftwarefoundryz"
def test_eco_compress(): r=_eco().context_compression("a"); assert r["ok"] and r["subsystem"]=="mem20rewardforgez"
def test_eco_events(): r=_eco().style_events("s",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().style_routing("k",["s"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_health_peer(): r=_eco().style_health_peer(); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_report_and_probe():
    m=_m(); rep=m.style_report(); assert rep["health"]["score"]==1.0 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
