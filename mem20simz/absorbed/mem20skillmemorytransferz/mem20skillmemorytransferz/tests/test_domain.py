import importlib
MOD="mem20skillmemorytransferz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_extract(): m=_m(); r=m.extract({"skills":{"s1":{"w":1}}},"s1"); assert r=={"w":1}
def test_transfer(): m=_m(); src={"skills":{"s1":{"w":1}}}; dst={}; r=m.transfer(src,dst,"s1"); assert r["ok"] is True
def test_merge(): m=_m(); r=m.merge_skills({"skills":{}},{"s2":{"w":2}}); assert "s2" in r["skills"]
def test_health(): m=_m(); r=m.transfer_health([{"ok":True},{"ok":False}]); assert r["ok"]==1
def test_estate_context_real_integrations(tmp_path):
    m=importlib.import_module("mem20skillmemorytransferz.domain"); ctx=m.estate_context(tmp_path/"store")
    assert ctx["engine_status_checked"] is True and ctx["work_recorded"] is True and ctx["path_scripts"]>=0
    assert "inventory_keys" in ctx and isinstance(ctx["focus_score"], float) and ctx["sitemap_skips_cache"] is True
def test_eco_graph(): r=_eco().skill_graph(); assert r["ok"] and r["subsystem"]=="mem20dynamicskillgraphz"
def test_eco_episodic(): r=_eco().episodic_memory(); assert r["ok"] and r["subsystem"]=="mem20episodicmemorygraphz"
def test_eco_time(): r=_eco().memory_timemachine(); assert r["ok"] and r["subsystem"]=="mem20memorytimemachinez"
def test_eco_events(): r=_eco().transfer_events("t",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_route(): r=_eco().transfer_routing("k",["t"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_contain(): r=_eco().transfer_containment("t"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_report_and_probe():
    m=_m(); rep=m.transfer_report(); assert rep["health"]["ok"]==1 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
