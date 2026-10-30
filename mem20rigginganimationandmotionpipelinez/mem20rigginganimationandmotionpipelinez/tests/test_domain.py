import importlib
MOD="mem20rigginganimationandmotionpipelinez"
def _m(): return importlib.import_module(MOD+".domain")
def test_rig(): m=_m(); r=m.create_rig(["bone1"]); assert "bone1" in r["bones"]
def test_pose(): m=_m(); r=m.create_rig(["bone1"]); m.set_pose(r,"bone1",(1,2,3)); assert r["pose"]["bone1"]== (1,2,3)
def test_anim(): m=_m(); r=m.create_rig(["bone1"]); res=m.animate(r,[{"pose":{"bone1":(5,0,0)}}]); assert len(res)==1
def test_blend(): m=_m(); r=m.motion_blend({"b1":(0,0,0)},{"b1":(10,0,0)},0.5); assert r["b1"][0]==5.0
def test_health(): m=_m(); r=m.create_rig(["bone1"]); assert m.rig_health(r)["bones"]==1
