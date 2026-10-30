import importlib
MOD="mem20realworldimpactrewardsz"
def _m(): return importlib.import_module(MOD+".domain")
def test_record(): m=_m(); r=m.record_impact({}, "u1", "plant", 5); assert "u1" in r
def test_reward(): m=_m(); r=m.record_impact({}, "u1", "plant", 5); assert m.compute_reward(r,"u1")==5.0
def test_lb(): m=_m(); r=m.record_impact({}, "u1", "plant", 5); lb=m.leaderboard(r); assert lb[0]["user"]=="u1"
def test_health(): m=_m(); r=m.record_impact({}, "u1", "plant", 5); assert m.impact_health(r)["users"]==1
