import importlib
MOD="mem20assetremixstudioz"
def _m(): return importlib.import_module(MOD+".domain")
def test_remix():
    m=_m(); r=m.remix([{"id":"a","metadata":{"x":1}}],["grayscale"]); assert "checksum" in r
def test_transform():
    m=_m(); r=m.transform_asset({"rotation":0},"rotate"); assert r["rotation"]==90
def test_export():
    m=_m(); r=m.export_formats({"id":"a","size":10},["png","jpg"]); assert len(r)==2
def test_blend():
    m=_m(); r=m.blend_assets({"metadata":{"x":10}},{"metadata":{"x":0}},0.5); assert "metadata" in r
def test_variants():
    m=_m(); r=m.remix_variants({"id":"a"},3); assert len(r)==3
