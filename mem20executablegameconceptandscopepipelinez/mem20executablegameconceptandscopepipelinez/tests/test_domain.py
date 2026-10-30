import importlib
MOD="mem20executablegameconceptandscopepipelinez"
def _m(): return importlib.import_module(MOD+".domain")
def test_score(): m=_m(); assert 0<=m.concept_score({"innovation":8,"market_fit":7,"feasibility":6})<=1
def test_scope(): m=_m(); r=m.scope_estimate({"features":["a","b"],"complexity":"high"}); assert r["weeks"]>0
def test_feas(): m=_m(); r=m.feasibility_check({"features":["a"],"complexity":"low"},10); assert "feasible" in r
def test_risk(): m=_m(); r=m.risk_assessment({"complexity":"high","market_fit":3,"team_size":2}); assert len(r)>0
def test_stage(): m=_m(); r=m.pipeline_stage({"innovation":9,"market_fit":9,"feasibility":9}); assert r=="greenlit"
