import importlib
MOD="mem20humancapabilitysuperplatformz"
def _m(): return importlib.import_module(MOD+".domain")
def test_assess(): m=_m(); r=m.assess("x",[{"weight":1,"value":0.8}]); assert 0<=r<=1
def test_growth(): m=_m(); r=m.growth_plan({"py":2},{"py":5,"js":3}); assert len(r)==2
def test_matrix(): m=_m(); r=m.capability_matrix([{"id":"u1","skills":{"py":3}}],["py"]); assert r["u1"]["py"]==3
def test_team(): m=_m(); r=m.team_capability({"u1":{"py":3},"u2":{"py":5}},"py"); assert r==4.0
def test_rec(): m=_m(); r=m.learning_recommendation([{"skill":"a","delta":2},{"skill":"b","delta":1}]); assert r[0]["skill"]=="a"
