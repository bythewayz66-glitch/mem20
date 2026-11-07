import importlib
MOD="mem20revenueleakhunterz"
def _m(): return importlib.import_module(MOD+".domain")
def test_detect(): m=_m(); r=m.detect_leaks([{"id":"t1","amount":90}],{"t1":100}); assert len(r)==1
def test_anom(): m=_m(); r=m.anomaly_score([1,2,3,100]); assert r>0
def test_rec(): m=_m(); r=m.detect_leaks([{"id":"t1","amount":90}],{"t1":100}); assert m.recoverable(r)==10
def test_health(): m=_m(); r=m.detect_leaks([{"id":"t1","amount":90}],{"t1":100}); assert m.hunter_health(r)["leaks"]==1

def test_estate_context_real_integrations(tmp_path):
    import importlib
    m = importlib.import_module("mem20revenueleakhunterz.domain")
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

