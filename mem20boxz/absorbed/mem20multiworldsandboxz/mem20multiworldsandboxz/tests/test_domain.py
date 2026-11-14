import importlib
MOD="mem20multiworldsandboxz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); w=m.create_world({"x":1},"w1"); assert w["name"]=="w1"
def test_branch(): m=_m(); w=m.create_world({"x":1}); c=m.branch(w,{"x":2}); assert c["state"]["x"]==2
def test_merge(): m=_m(); a=m.create_world({"x":1}); b=m.create_world({"y":2}); r=m.merge([a,b]); assert "x" in r["state"] or "y" in r["state"]
def test_step(): m=_m(); w=m.create_world({}); m.step(w,{"name":"a","effect":{"x":5}}); assert w["state"]["x"]==5
def test_health(): m=_m(); r=m.world_health([m.create_world({})]); assert r["count"]==1
