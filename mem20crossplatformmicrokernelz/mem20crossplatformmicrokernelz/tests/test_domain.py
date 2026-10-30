import importlib
MOD="mem20crossplatformmicrokernelz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); p=m.create_process(1); assert p["pid"]==1
def test_alloc(): m=_m(); p=m.create_process(1); m.allocate_memory(p,[1,2]); assert len(p["memory_pages"])==2
def test_ipc(): m=_m(); r=m.ipc_send(1,2,"hi"); assert r["delivered"] is True
def test_sched(): m=_m(); r=m.schedule([{"pid":1,"state":"ready","priority":1},{"pid":2,"state":"ready","priority":2}]); assert r[0]["pid"]==2
def test_kill(): m=_m(); p=m.create_process(1); m.kill(p); assert p["state"]=="terminated"
