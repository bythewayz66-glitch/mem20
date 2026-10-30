import importlib
MOD="mem20selfhealingruntimecivilizationz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_civilization(["a","b"]); assert len(r["agents"])==2
def test_damage(): m=_m(); r=m.create_civilization(["a"]); m.damage(r,"a",0.5); assert r["agents"]["a"]["health"]==0.5
def test_heal(): m=_m(); r=m.create_civilization(["a"]); m.damage(r,"a",0.5); m.heal(r,"a",0.3); assert r["agents"]["a"]["health"]==0.8
def test_auto(): m=_m(); r=m.create_civilization(["a"]); m.damage(r,"a",0.9); m.auto_heal(r,0.3,0.5); assert r["agents"]["a"]["health"]>=0.5
def test_health(): m=_m(); r=m.create_civilization(["a"]); assert "alive" in m.civ_health(r)
