import importlib
MOD="mem20styleguideagentz"
def _m(): return importlib.import_module(MOD+".domain")
def test_check(): m=_m(); r=m.check("hello world", [{"type":"max_length","value":5}]); assert len(r)==1
def test_fix(): m=_m(); r=m.fix("hello",""); assert r=="hello"
def test_score(): m=_m(); r=m.style_score("hi", [{"type":"max_length","value":5}]); assert r==1.0
def test_health(): m=_m(); r=m.style_health("hi", [{"type":"max_length","value":5}]); assert r["score"]==1.0
