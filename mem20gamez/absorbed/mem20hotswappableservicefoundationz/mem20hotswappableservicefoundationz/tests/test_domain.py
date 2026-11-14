import importlib
MOD="mem20hotswappableservicefoundationz"
def _m(): return importlib.import_module(MOD+".domain")
def test_register(): m=_m(); r=m.register_service({}, "svc", "impl1"); assert "svc" in r["services"]
def test_swap(): m=_m(); r=m.register_service({}, "svc", "impl1"); m.swap(r, "svc", "impl2"); assert r["services"]["svc"]["version"]==2
def test_health(): m=_m(); r=m.register_service({}, "svc", "impl1"); h=m.health(r); assert h["active"]==1
def test_rollback(): m=_m(); r=m.register_service({}, "svc", "impl1"); m.swap(r, "svc", "impl2"); m.rollback(r, "svc"); assert r["services"]["svc"]["version"]==1
def test_list(): m=_m(); r=m.register_service({}, "svc", "impl1"); assert "svc" in m.list_services(r)
