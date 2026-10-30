import importlib
MOD="mem20edgetransportfabricz"
def _m(): return importlib.import_module(MOD+".domain")
def test_route(): m=_m(); r=m.route_path("a","b",{"a":["b"]}); assert r==["a","b"]
def test_qos(): m=_m(); assert m.qos_class(10,2)=="premium"
def test_alloc(): m=_m(); r=m.allocate_bandwidth(100,[{"id":"a","demand":1},{"id":"b","demand":1}]); assert len(r)==2
def test_health(): m=_m(); r=m.transport_health([{"status":"up"},{"status":"down"}]); assert r["up"]==1
