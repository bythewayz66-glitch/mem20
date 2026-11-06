import importlib
MOD="mem20specialistmodelforgez"
def _m(): return importlib.import_module(MOD+".domain")
def test_forge(): m=_m(); r=m.forge("base","code",["d1"]); assert "code" in r["name"]
def test_eval(): m=_m(); r=m.forge("base","code",["d1"]); assert 0<=m.evaluate(r,["t"])<=1
def test_merge(): m=_m(); a=m.forge("base","code",["d1"]); b=m.forge("base","math",["d2"]); r=m.merge_specialists([a,b]); assert "merged" in r["name"]
def test_health(): m=_m(); r=m.forge("base","code",["d1"]); assert m.forge_health([r])["models"]==1

def test_estate_context_real_integrations(tmp_path):
    import importlib
    m = importlib.import_module("mem20specialistmodelforgez.domain")
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

