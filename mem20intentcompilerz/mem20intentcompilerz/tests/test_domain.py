import importlib
MOD="mem20intentcompilerz"
def _m(): return importlib.import_module(MOD+".domain")
def test_parse(): m=_m(); r=m.parse_intent("create user"); assert r["verb"]=="create"
def test_classify(): m=_m(); assert m.classify({"verb":"create","object":"x","raw":"create x"})=="mutation"
def test_compile(): m=_m(); r=m.compile_to_action({"verb":"list","object":"users","raw":"list users"}); assert r["action"]=="list"
def test_validate(): m=_m(); assert m.validate({"verb":"create","object":"x","raw":"create x"}) is True
def test_conf(): m=_m(); r=m.intent_confidence({"raw":"create user now"},["create","user"]); assert 0<=r<=1
