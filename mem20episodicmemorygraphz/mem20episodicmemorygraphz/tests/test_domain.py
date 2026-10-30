import importlib
MOD="mem20episodicmemorygraphz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); e=m.create_episode("t"); assert e["title"]=="t"
def test_add(): m=_m(); e=m.create_episode("t"); m.add_event(e,{"x":1}); assert len(e["events"])==1
def test_link(): m=_m(); e1=m.create_episode("a"); e2=m.create_episode("b"); m.link_episodes([e1,e2],e1["id"],e2["id"]); assert len(e1.get("links",[]))==1
def test_recall(): m=_m(); e=m.create_episode("hello world"); r=m.recall([e],"hello"); assert len(r)==1
def test_graph(): m=_m(); e=m.create_episode("t"); r=m.episode_graph([e]); assert "nodes" in r
