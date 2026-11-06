import importlib
MOD="mem20universalhealthnervoussystemz"
def _m(): return importlib.import_module(MOD+".domain")
def test_reg(): m=_m(); r=m.register_subsystem({}, "s1", lambda: {"ok": True}); assert "s1" in r["subsystems"]
def test_check(): m=_m(); r=m.register_subsystem({}, "s1", lambda: {"ok": True}); m.check_all(r); assert r["subsystems"]["s1"]["status"]=="healthy"
def test_overall(): m=_m(); r=m.register_subsystem({}, "s1", lambda: {"ok": True}); m.check_all(r); assert m.overall(r)=="healthy"
def test_report(): m=_m(); r=m.register_subsystem({}, "s1", lambda: {"ok": True}); m.check_all(r); assert "overall" in m.health_report(r)

def test_estate_context_real_integrations(tmp_path):
    import importlib
    m = importlib.import_module("mem20universalhealthnervoussystemz.domain")
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

