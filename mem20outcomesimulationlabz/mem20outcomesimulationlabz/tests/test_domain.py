import importlib
MOD="mem20outcomesimulationlabz"
def _m(): return importlib.import_module(MOD+".domain")
def test_sim(): m=_m(); r=m.simulate_once({"base":100,"std":5},seed=1); assert isinstance(r,float)
def test_mc(): m=_m(); r=m.monte_carlo({"base":100,"std":5},n=10,seed=1); assert len(r)==10
def test_sum(): m=_m(); r=m.summarize([1.0,2.0,3.0]); assert "mean" in r
def test_compare(): m=_m(); r=m.scenario_compare([{"name":"a","params":{"base":100,"std":5},"seed":1}]); assert r[0]["name"]=="a"
def test_risk(): m=_m(); r=m.risk_of_loss([5, -1, 3],0); assert 0<=r<=1
