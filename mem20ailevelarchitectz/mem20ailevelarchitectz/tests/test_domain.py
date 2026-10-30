import importlib
MOD="mem20ailevelarchitectz"
def _m(): return importlib.import_module(MOD+".domain")
def test_layout():
    m=_m(); r=m.generate_layout(20,20,4,1); assert len(r["rooms"])==4
def test_difficulty():
    m=_m(); r=m.difficulty_curve(3); assert len(r)==3
def test_place_enemies():
    m=_m(); layout=m.generate_layout(20,20,2,1); r=m.place_enemies(layout,0.5,1); assert isinstance(r,list)
def test_pacing():
    m=_m(); r=m.pacing_profile(100,4); assert len(r)==4
def test_validate():
    m=_m(); r=m.validate_level({"width":10,"height":10,"rooms":[{"w":3,"h":3}]}); assert r["valid"] is True
