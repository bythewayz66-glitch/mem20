import importlib
MOD="mem20selfhealingplansz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_plan(["s1","s2"]); assert len(r["steps"])==2
def test_exec(): m=_m(); r=m.create_plan(["s1"]); m.execute_step(r,0,lambda n: None); assert r["steps"][0]["status"]=="done"
def test_heal(): m=_m(); r=m.create_plan(["s1"]); m.execute_step(r,0,lambda n: (_ for _ in ()).throw(Exception("boom"))); assert r["steps"][0]["status"]=="failed"; m.heal_plan(r); assert r["steps"][0]["status"]=="pending"
def test_status(): m=_m(); r=m.create_plan(["s1"]); m.execute_step(r,0,lambda n: None); assert m.plan_status(r)["done"]==1

def test_estate_context_real_integrations(tmp_path):
    import importlib
    m = importlib.import_module("mem20selfhealingplansz.domain")
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

