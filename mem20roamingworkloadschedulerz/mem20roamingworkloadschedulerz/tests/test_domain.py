import importlib
MOD="mem20roamingworkloadschedulerz"
def _m(): return importlib.import_module(MOD+".domain")
def test_sched(): m=_m(); nodes=[{"id":"n1","load":0},{"id":"n2","load":5}]; r=m.schedule([{"id":"w1","cost":2}],nodes); assert r[0]["node"]=="n1"
def test_mig(): m=_m(); r=m.migrate("w1","n1","n2"); assert r["to"]=="n2"
def test_load(): m=_m(); r=m.node_load([{"id":"n1","load":3}]); assert r["n1"]==3
def test_health(): m=_m(); r=m.scheduler_health([{"id":"n1","load":3}]); assert r["nodes"]==1

def test_estate_context_real_integrations(tmp_path):
    import importlib
    m = importlib.import_module("mem20roamingworkloadschedulerz.domain")
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

