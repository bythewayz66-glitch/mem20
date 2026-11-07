import importlib
MOD="mem20runtimepromptoptimizerz"
def _m(): return importlib.import_module(MOD+".domain")
def test_tok(): m=_m(); assert m.tokenize("a b")==["a","b"]
def test_comp(): m=_m(); r=m.compress("a b c d",2); assert "..." in r
def test_score(): m=_m(); r=m.score_prompt("hello world",{"hello":1}); assert r==1
def test_opt(): m=_m(); r=m.optimize("hello world foo",{"hello":1},2); assert "prompt" in r
def test_health(): m=_m(); r=m.prompt_health(["a b","c d e"]); assert r["count"]==2

def test_estate_context_real_integrations(tmp_path):
    import importlib
    m = importlib.import_module("mem20runtimepromptoptimizerz.domain")
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

