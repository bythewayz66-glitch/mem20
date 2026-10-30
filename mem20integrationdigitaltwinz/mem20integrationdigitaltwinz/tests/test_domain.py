import importlib
MOD="mem20integrationdigitaltwinz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); t=m.create_twin({"id":"s1","state":{"x":1}}); assert t["id"]=="s1"
def test_sync(): m=_m(); t=m.create_twin({"id":"s1","state":{}}); m.sync(t,{"x":5}); assert t["state"]["x"]==5
def test_sim(): m=_m(); t=m.create_twin({"id":"s1","state":{}}); r=m.simulate(t,[{"name":"a","effect":{"x":1}}]); assert len(r)==1
def test_drift(): m=_m(); t=m.create_twin({"id":"s1","state":{"x":1}}); r=m.drift(t,{"x":2}); assert "x" in r
def test_health(): m=_m(); t=m.create_twin({"id":"s1"}); r=m.health(t); assert "synced" in r
