import importlib
MOD="mem20edgefleetbrainz"
def _m(): return importlib.import_module(MOD+".domain")
def test_register(): m=_m(); f=m.register_device({"devices":[]}, {"id":"d1","capacity":10}); assert len(f["devices"])==1
def test_place(): m=_m(); f=m.register_device({"devices":[]}, {"id":"d1","capacity":10,"status":"online","load":0}); w={"size":5}; r=m.place_workload(f,w); assert r["id"]=="d1"
def test_health(): m=_m(); f=m.register_device({"devices":[]}, {"id":"d1","capacity":10,"status":"online"}); r=m.fleet_health(f); assert r["health"]==1.0
def test_evict(): m=_m(); f={"devices":[{"id":"d1","status":"online","last_seen":0}]}; r=m.evict_offline(f,10); assert "remaining" in r
def test_now(): m=_m(); assert isinstance(m.time_now(), float)
