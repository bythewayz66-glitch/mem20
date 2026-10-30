import importlib
MOD="mem20skillbasedprogressionbrainz"
def _m(): return importlib.import_module(MOD+".domain")
def test_xp(): m=_m(); r=m.gain_xp({"xp":0},100); assert r["xp"]==100
def test_unlock(): m=_m(); r=m.gain_xp({"xp":0,"skills":[]},50); res=m.unlock_skill(r,"s1",30); assert res["ok"] is True
def test_level(): m=_m(); r=m.gain_xp({"xp":0,"level":1},100); assert m.level(r)>=1
def test_health(): m=_m(); r=m.gain_xp({"xp":0},10); assert "level" in m.progression_health(r)
