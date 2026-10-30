import importlib
MOD="mem20servicebundlingenginez"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_bundle([{"price":5},{"price":3}]); assert r["price"]==8
def test_add(): m=_m(); r=m.create_bundle([]); m.add_service(r,{"price":4}); assert r["price"]==4
def test_disc(): m=_m(); r=m.create_bundle([{"price":10}]); m.discount(r,0.1); assert r["price"]==9.0
def test_health(): m=_m(); r=m.bundle_health([m.create_bundle([])]); assert r["bundles"]==1
