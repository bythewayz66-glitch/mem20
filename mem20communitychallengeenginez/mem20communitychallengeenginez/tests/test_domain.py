import importlib
MOD="mem20communitychallengeenginez"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); c=m.create_challenge("c",100); assert c["name"]=="c"
def test_join(): m=_m(); c=m.create_challenge("c",100); m.join(c,"u1"); assert "u1" in c["participants"]
def test_progress(): m=_m(); c=m.create_challenge("c",100); m.join(c,"u1"); m.record_progress(c,"u1",50); assert c["participants"]["u1"]==50
def test_leaderboard(): m=_m(); c=m.create_challenge("c",100); m.join(c,"u1"); m.join(c,"u2"); m.record_progress(c,"u1",30); m.record_progress(c,"u2",50); lb=m.leaderboard(c); assert lb[0]["user"]=="u2"
def test_completion(): m=_m(); c=m.create_challenge("c",100); m.join(c,"u1"); m.record_progress(c,"u1",100); r=m.check_completion(c); assert r["completed"] is True
