import importlib
MOD="mem20productledgrowthsimulatorz"
def _m(): return importlib.import_module(MOD+".domain")
def test_funnel(): m=_m(); r=m.funnel(100,[{"conversion":0.5},{"conversion":0.5}]); assert r[-1]==25
def test_viral(): m=_m(); r=m.viral_coefficient(2,0.1); assert r==0.2
def test_ret(): m=_m(); r=m.retention_curve(100,0.1,3); assert len(r)==4
def test_score(): m=_m(); r=m.growth_score({"viral_k":0.2,"conversion":0.3,"retention":0.4}); assert 0<=r<=1
def test_sim(): m=_m(); r=m.simulate({"starting_users":100,"invites":2,"invite_conv":0.1}); assert "after_viral" in r
