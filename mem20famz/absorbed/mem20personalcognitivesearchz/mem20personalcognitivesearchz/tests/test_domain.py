import importlib
MOD="mem20personalcognitivesearchz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_index(): m=_m(); idx=m.index([{"id":"d1","text":"hello world"}]); assert "hello" in idx
def test_query(): m=_m(); idx=m.index([{"id":"d1","text":"hello world"}]); docs={"d1":{"id":"d1","text":"hello world"}}; r=m.query(idx,"hello",docs); assert len(r)==1
def test_rank(): m=_m(); r=m.rank([{"text":"hello world"},{"text":"hello"}],"hello"); assert len(r)==2
def test_recall(): m=_m(); r=m.recall({},["a","b"],2); assert len(r)==2
def test_health(): m=_m(); idx=m.index([{"id":"d1","text":"hi"}]); r=m.search_health(idx); assert r["terms"]==1

def test_estate_context_real_integrations(tmp_path):
    m=_m(); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True

def test_eco_episodic(): r=_eco().episodic_memory(); assert r["ok"] and r["subsystem"]=="mem20episodicmemorygraphz"
def test_eco_compress(): r=_eco().context_compress("q"); assert r["ok"] and r["subsystem"]=="mem20rewardforgez"
def test_eco_recall(): r=_eco().predictive_recall(); assert r["ok"] and r["subsystem"]=="mem20predictiverecallenginez"
def test_eco_events(): r=_eco().search_events("s",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().search_routing("k",["s"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_compile(): r=_eco().output_compile(); assert r["ok"] and r["subsystem"]=="mem20agentoutputcompilerz"
def test_report_and_probe():
    m=_m(); rep=m.cogsearch_report(); assert rep["hits"]==1 and rep["health"]["terms"]>=1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
