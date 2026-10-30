import importlib
MOD="mem20multibrandswarmz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_swarm(["a","b"]); assert "a" in r["brands"]
def test_agent(): m=_m(); r=m.create_swarm(["a"]); m.add_agent(r,"a","ag1"); assert "ag1" in r["brands"]["a"]["agents"]
def test_campaign(): m=_m(); r=m.create_swarm(["a"]); m.launch_campaign(r,"a","c1"); assert len(r["brands"]["a"]["campaigns"])==1
def test_cross(): m=_m(); r=m.create_swarm(["a","b"]); m.cross_promote(r,["a","b"],"asset"); assert "asset" in r["shared_assets"]
def test_health(): m=_m(); r=m.create_swarm(["a"]); assert m.swarm_health(r)["brands"]==1
