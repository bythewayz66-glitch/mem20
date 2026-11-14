import importlib
MOD="mem20asynccollaborationcapsulesz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create():
    m=_m(); c=m.create_capsule("c",["u1"]); assert c["name"]=="c"
def test_apply():
    m=_m(); c=m.create_capsule("c",["u1"]); r=m.apply_change(c,"u1",{"x":1}); assert r["ok"] is True
def test_sync():
    m=_m(); c=m.create_capsule("c",["u1"]); m.apply_change(c,"u1",{"x":1}); r=m.sync(c,0,{"y":2}); assert "merged" in r
def test_merge():
    m=_m(); c1=m.create_capsule("a",["u1"]); c2=m.create_capsule("b",["u2"]); r=m.merge_capsules(c1,c2); assert "u1" in r["members"]
def test_checksum():
    m=_m(); c=m.create_capsule("c",[]); assert len(m.capsule_checksum(c))==12
