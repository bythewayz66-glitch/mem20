import importlib
MOD="mem20multibrandswarmz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_swarm(["a","b"]); assert "a" in r["brands"]
def test_agent(): m=_m(); r=m.create_swarm(["a"]); m.add_agent(r,"a","ag1"); assert "ag1" in r["brands"]["a"]["agents"]
def test_campaign(): m=_m(); r=m.create_swarm(["a"]); m.launch_campaign(r,"a","c1"); assert len(r["brands"]["a"]["campaigns"])==1
def test_cross(): m=_m(); r=m.create_swarm(["a","b"]); m.cross_promote(r,["a","b"],"asset"); assert "asset" in r["shared_assets"]
def test_health(): m=_m(); r=m.create_swarm(["a"]); assert m.swarm_health(r)["brands"]==1

from mem20multibrandswarmz import ecosystem
def _assert_signal(sig):
 assert isinstance(sig,dict) and "subsystem" in sig and "ok" in sig
 if not sig["ok"]: assert "error" in sig
def test_analyze_swarm():
 m=_m(); r=m.analyze_swarm({"brands":["x","y"],"shared_infrastructure":["auth"]})
 assert r["ok"] and r["portfolio"]["brand_count"]==2 and r["isolation"]["audiences_distinct"]
def test_ecosystem():
 c={"brand":"x"}; _assert_signal(ecosystem.offer_assembly_signal(c)); _assert_signal(ecosystem.compounding_product_signal(c)); _assert_signal(ecosystem.business_model_signal(c)); _assert_signal(ecosystem.goal_economy_signal(c)); _assert_signal(ecosystem.eventstream_signal(c)); _assert_signal(ecosystem.capability_market_signal(c))
 r=ecosystem.swarm_signals(c); assert set(r["checks"].keys())=={"offer_assembly","compounding_product","business_model","goal_economy","eventstream","capability_market"}
 for v in r["checks"].values(): _assert_signal(v)
