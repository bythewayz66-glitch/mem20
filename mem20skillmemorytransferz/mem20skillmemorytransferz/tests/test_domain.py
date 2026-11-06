import importlib
MOD="mem20skillmemorytransferz"
def _m(): return importlib.import_module(MOD+".domain")
def test_extract(): m=_m(); r=m.extract({"skills":{"s1":{"w":1}}},"s1"); assert r=={"w":1}
def test_transfer(): m=_m(); src={"skills":{"s1":{"w":1}}}; dst={}; r=m.transfer(src,dst,"s1"); assert r["ok"] is True
def test_merge(): m=_m(); r=m.merge_skills({"skills":{}},{"s2":{"w":2}}); assert "s2" in r["skills"]
def test_health(): m=_m(); r=m.transfer_health([{"ok":True},{"ok":False}]); assert r["ok"]==1

def test_estate_context_real_integrations(tmp_path):
    import importlib
    m = importlib.import_module("mem20skillmemorytransferz.domain")
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

