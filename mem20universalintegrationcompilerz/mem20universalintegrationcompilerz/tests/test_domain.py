import importlib
MOD="mem20universalintegrationcompilerz"
def _m(): return importlib.import_module(MOD+".domain")
def test_compile(): m=_m(); r=m.compile_integration("a","b",{"x":"y"}); assert r["compiled"] is True
def test_validate(): m=_m(); r=m.validate_mapping({"x":"y"},{"x":1},{"y":1}); assert r["valid"] is True
def test_transform(): m=_m(); r=m.transform({"x":5},{"x":"y"}); assert r["y"]==5
def test_health(): m=_m(); r=m.integration_health([{"compiled":True}]); assert r["integrations"]==1

def test_estate_context_real_integrations(tmp_path):
    m = _m()
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

