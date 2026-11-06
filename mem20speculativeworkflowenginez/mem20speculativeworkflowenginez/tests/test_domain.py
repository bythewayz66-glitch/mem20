import importlib
MOD="mem20speculativeworkflowenginez"
def _m(): return importlib.import_module(MOD+".domain")
def test_spec(): m=_m(); r=m.speculate({},["b1","b2"]); assert len(r)==2
def test_commit(): m=_m(); r=m.speculate({},["b1","b2"]); m.commit(r,"b1"); assert r[0]["status"]=="committed"
def test_roll(): m=_m(); r=m.speculate({},["b1"]); m.commit(r,"b1"); m.rollback(r); assert r[0]["status"]=="rolled_back"
def test_health(): m=_m(); r=m.speculate({},["b1"]); m.commit(r,"b1"); assert m.speculative_health(r)["committed"]==1

def test_estate_context_real_integrations(tmp_path):
    import importlib
    m = importlib.import_module("mem20speculativeworkflowenginez.domain")
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

