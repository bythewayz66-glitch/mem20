import importlib
MOD="mem20visualagentblackboardz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_blackboard("bb"); assert r["name"]=="bb"
def test_post(): m=_m(); r=m.create_blackboard("bb"); m.post(r,"a1","item"); assert len(r["items"])==1
def test_read(): m=_m(); r=m.create_blackboard("bb"); m.post(r,"a1","item"); assert len(m.read(r))==1
def test_clear(): m=_m(); r=m.create_blackboard("bb"); m.post(r,"a1","item"); m.clear(r); assert len(r["items"])==0
def test_health(): m=_m(); r=m.create_blackboard("bb"); m.post(r,"a1","item"); assert m.blackboard_health(r)["items"]==1
