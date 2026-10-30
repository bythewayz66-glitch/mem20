import importlib
MOD="mem20securecomputecapsulesz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_capsule("print(1)"); assert r["status"]=="created"
def test_run(): m=_m(); r=m.create_capsule("x"); m.run_capsule(r,lambda code,limits: 42); assert r["status"]=="completed"
def test_iso(): m=_m(); r=m.create_capsule("x"); m.isolate(r); assert r["isolated"] is True
def test_health(): m=_m(); r=m.create_capsule("x"); m.run_capsule(r,lambda c,l: 1); assert m.capsule_health([r])["completed"]==1
