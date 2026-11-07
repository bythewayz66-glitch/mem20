import importlib
MOD="mem20runtimecompatibilityenginez"
def _m(): return importlib.import_module(MOD+".domain")
def test_py(): m=_m(); assert m.check_python((3,0)) is True
def test_deps(): m=_m(); r=m.check_deps(["a","b"],["a"]); assert r["ok"] is False
def test_report(): m=_m(); r=m.compatibility_report({"installed":["a"]},{"python":(3,0),"deps":["a"]}); assert r["compatible"] is True
def test_fixes(): m=_m(); r=m.compatibility_report({"installed":[]},{"python":(3,0),"deps":["a"]}); assert "install a" in m.suggest_fixes(r)

def test_estate_context_real_integrations(tmp_path):
    import importlib
    m = importlib.import_module("mem20runtimecompatibilityenginez.domain")
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

