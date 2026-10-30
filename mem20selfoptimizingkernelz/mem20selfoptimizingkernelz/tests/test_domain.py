import importlib
MOD="mem20selfoptimizingkernelz"
def _m(): return importlib.import_module(MOD+".domain")
def test_opt(): m=_m(); r=m.optimize({"x":0.5},{"x":1.0}); assert r["x"]>0.5
def test_score(): m=_m(); r=m.score({"x":2},{"x":3}); assert r==6
def test_search(): m=_m(); r=m.search({"x":[1,2,3]},{"x":2},5,seed=1); assert "params" in r
def test_health(): m=_m(); r=m.kernel_health({"a":1}); assert r["params"]==1
