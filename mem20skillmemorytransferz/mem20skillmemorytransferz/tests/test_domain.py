import importlib
MOD="mem20skillmemorytransferz"
def _m(): return importlib.import_module(MOD+".domain")
def test_extract(): m=_m(); r=m.extract({"skills":{"s1":{"w":1}}},"s1"); assert r=={"w":1}
def test_transfer(): m=_m(); src={"skills":{"s1":{"w":1}}}; dst={}; r=m.transfer(src,dst,"s1"); assert r["ok"] is True
def test_merge(): m=_m(); r=m.merge_skills({"skills":{}},{"s2":{"w":2}}); assert "s2" in r["skills"]
def test_health(): m=_m(); r=m.transfer_health([{"ok":True},{"ok":False}]); assert r["ok"]==1
