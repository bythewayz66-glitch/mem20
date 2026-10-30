import importlib
MOD="mem20dynamicnarrativeenginez"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); s=m.create_story("start"); assert s["current"]=="start"
def test_add(): m=_m(); s=m.create_story("start"); m.add_node(s,"end","The end",[]); assert "end" in s["nodes"]
def test_choose(): m=_m(); s=m.create_story("start"); m.add_node(s,"start","Hi",[{"target":"end","effects":{"mood":"happy"}}]); m.add_node(s,"end","Bye",[]); m.choose(s,0); assert s["current"]=="end"
def test_text(): m=_m(); s=m.create_story("start"); m.add_node(s,"start","Hello",[]); assert m.current_text(s)=="Hello"
def test_state(): m=_m(); s=m.create_story("start"); r=m.narrative_state(s); assert "total_nodes" in r
