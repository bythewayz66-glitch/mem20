import importlib
MOD="mem20playermotivationtwinz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_twin("p1"); assert r["player"]=="p1"
def test_update(): m=_m(); r=m.create_twin("p1"); m.update(r,{"delta":0.2}); assert r["motivation"]==0.7
def test_churn(): m=_m(); r=m.create_twin("p1"); m.update(r,{"delta":-0.5}); assert m.predict_churn(r) is True
def test_seg(): m=_m(); r=m.create_twin("p1"); m.update(r,{"delta":0.3}); assert m.motivation_segments(r)=="high"
def test_health(): m=_m(); r=m.create_twin("p1"); assert "motivation" in m.twin_health(r)
