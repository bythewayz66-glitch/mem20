import importlib
MOD="mem20securecomputecapsulesz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_capsule("print(1)"); assert r["status"]=="created"
def test_run(): m=_m(); r=m.create_capsule("x"); m.run_capsule(r,lambda code,limits: 42); assert r["status"]=="completed"
def test_iso(): m=_m(); r=m.create_capsule("x"); m.isolate(r); assert r["isolated"] is True
def test_health(): m=_m(); r=m.create_capsule("x"); m.run_capsule(r,lambda c,l: 1); assert m.capsule_health([r])["completed"]==1

def test_estate_context_real_integrations(tmp_path):
    import importlib
    m = importlib.import_module("mem20securecomputecapsulesz.domain")
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

