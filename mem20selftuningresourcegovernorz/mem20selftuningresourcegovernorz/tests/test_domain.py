import importlib
MOD="mem20selftuningresourcegovernorz"
def _m(): return importlib.import_module(MOD+".domain")
def test_gov(): m=_m(); r=m.govern({"cpu":10},{"cpu":9},{"cpu":0.8}); assert len(r)==1
def test_adj(): m=_m(); r=m.adjust_quota("cpu",10,0.9); assert r==12.0
def test_health(): m=_m(); r=m.governor_health({"cpu":10},{"cpu":9}); assert r["overloaded"]==1
