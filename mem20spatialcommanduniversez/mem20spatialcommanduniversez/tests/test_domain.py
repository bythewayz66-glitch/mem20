import importlib
MOD="mem20spatialcommanduniversez"
def _m(): return importlib.import_module(MOD+".domain")
def test_region(): m=_m(); r=m.create_region("r1",[(0,10),(0,10)]); assert r["name"]=="r1"
def test_add(): m=_m(); r=m.create_region("r1",[(0,10),(0,10)]); m.add_entity(r,"e1",(5,5)); assert len(r["entities"])==1
def test_dist(): m=_m(); assert m.distance((0,0),(3,4))==5.0
def test_in(): m=_m(); r=m.create_region("r1",[(0,10),(0,10)]); assert m.in_region(r,(5,5)) is True
def test_health(): m=_m(); r=m.create_region("r1",[(0,10),(0,10)]); assert m.spatial_health([r])["regions"]==1

def test_estate_context_real_integrations(tmp_path):
    import importlib
    m = importlib.import_module("mem20spatialcommanduniversez.domain")
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

