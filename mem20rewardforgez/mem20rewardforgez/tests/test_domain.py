import importlib
MOD="mem20rewardforgez"
def _m(): return importlib.import_module(MOD+".domain")
def test_linear(): m=_m(); r=m.linear_reward({"x":2,"y":3},{"x":1,"y":2}); assert r==8
def test_shaped(): m=_m(); r=m.shaped_reward(5,2); assert r==7
def test_norm(): m=_m(); r=m.normalize([0,5,10]); assert r==[0.0,0.5,1.0]
def test_health(): m=_m(); r=m.reward_health([1,2,3]); assert r["count"]==3
