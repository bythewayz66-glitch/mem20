import importlib
MOD="mem20sensorymemoryingestz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_ingest(): m=_m(); r=m.ingest({"entries":[]},"hi","text"); assert r["modality"]=="text"
def test_filter(): m=_m(); s={"entries":[]}; m.ingest(s,"hi","text"); m.ingest(s,"img","image"); r=m.filter_by_modality(s,"text"); assert len(r)==1
def test_recent(): m=_m(); s={"entries":[]}; m.ingest(s,"a","text"); r=m.recent(s,5); assert len(r)==1
def test_health(): m=_m(); s={"entries":[]}; m.ingest(s,"a","text"); r=m.ingest_health(s); assert r["entries"]==1

def test_estate_context_real_integrations(tmp_path):
    import importlib
    m = importlib.import_module("mem20sensorymemoryingestz.domain")
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

def test_eco_episodic(): r=_eco().episodic_store("s",{"v":1}); assert r["ok"] and r["subsystem"]=="mem20episodicmemorygraphz"
def test_eco_events(): r=_eco().ingest_events("i",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_compress(): r=_eco().context_compression("a"); assert r["ok"] and r["subsystem"]=="mem20contextcompressionforgez"
def test_eco_route(): r=_eco().ingest_routing("k",["i"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_health_peer(): r=_eco().health_nervous(); assert r["ok"] and r["subsystem"]=="mem20universalhealthnervoussystemz"
def test_eco_contain(): r=_eco().ingest_containment("i"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_report_and_probe():
    m=_m(); rep=m.ingest_report(); assert rep["health"]["entries"]==2 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"]
