import importlib
MOD="mem20resourceexchangemarketz"
def _m(): return importlib.import_module(MOD+".domain")
def test_list(): m=_m(); r=m.list_resource("s","cpu",10,5); assert r["available"] is True
def test_buy(): m=_m(); r=m.list_resource("s","cpu",10,5); res=m.buy(r,"b",3); assert res["ok"] is True
def test_price(): m=_m(); r=m.list_resource("s","cpu",10,5); m.buy(r,"b",3); assert r["amount"]==7
def test_health(): m=_m(); r=m.market_health([m.list_resource("s","cpu",10,5)]); assert r["listings"]==1

def test_estate_context_real_integrations(tmp_path):
    import importlib
    m = importlib.import_module("mem20resourceexchangemarketz.domain")
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

