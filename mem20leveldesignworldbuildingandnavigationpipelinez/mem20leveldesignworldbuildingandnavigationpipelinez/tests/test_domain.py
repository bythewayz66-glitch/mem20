import importlib
MOD="mem20leveldesignworldbuildingandnavigationpipelinez"
def _m(): return importlib.import_module(MOD+".domain")
def test_navmesh(): m=_m(); r=m.generate_navmesh([[0,1],[0,0]]); assert (0,0) in r
def test_path(): m=_m(); r=m.pathfind([[0,0],[0,0]],(0,0),(1,1)); assert len(r)>0
def test_props(): m=_m(); r=m.place_props({"width":5,"height":5},["tree"],1); assert len(r)==1
def test_validate(): m=_m(); r=m.validate_level({"rooms":[{"w":1,"h":1}]}); assert r["valid"] is True
