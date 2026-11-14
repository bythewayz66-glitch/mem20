import importlib
MOD="mem20ambientdevicecompanionz"
def _m(): return importlib.import_module(MOD+".domain")
def test_sense():
    m=_m(); assert m.sense_context({"hour":23,"motion":0.0,"location":"home"})=="sleeping"
def test_suggest():
    m=_m(); assert m.proactive_suggestion("commuting",[])=="play podcast"
def test_routine():
    m=_m(); r=m.routine_match("idle",[{"trigger_context":"idle","action":"x"}]); assert r is not None
def test_mood():
    m=_m(); assert m.companion_mood({"battery":0.1})=="concerned"
def test_score():
    m=_m(); assert 0<=m.ambient_score({"motion":0.5,"interaction":0.5})<=1
