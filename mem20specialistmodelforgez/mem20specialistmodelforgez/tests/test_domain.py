import importlib
MOD="mem20specialistmodelforgez"
def _m(): return importlib.import_module(MOD+".domain")
def test_forge(): m=_m(); r=m.forge("base","code",["d1"]); assert "code" in r["name"]
def test_eval(): m=_m(); r=m.forge("base","code",["d1"]); assert 0<=m.evaluate(r,["t"])<=1
def test_merge(): m=_m(); a=m.forge("base","code",["d1"]); b=m.forge("base","math",["d2"]); r=m.merge_specialists([a,b]); assert "merged" in r["name"]
def test_health(): m=_m(); r=m.forge("base","code",["d1"]); assert m.forge_health([r])["models"]==1
