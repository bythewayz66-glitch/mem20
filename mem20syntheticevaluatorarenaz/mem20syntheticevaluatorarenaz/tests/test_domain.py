import importlib
MOD="mem20syntheticevaluatorarenaz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_arena(["a","b"]); assert len(r["agents"])==2
def test_eval(): m=_m(); r=m.create_arena(["a","b"]); m.evaluate(r,"a","b",0.9); assert len(r["evaluations"])==1
def test_lb(): m=_m(); r=m.create_arena(["a","b"]); m.evaluate(r,"a","b",0.9); lb=m.leaderboard(r); assert lb[0]["agent"]=="b"
def test_health(): m=_m(); r=m.create_arena(["a","b"]); assert m.arena_health(r)["agents"]==2
