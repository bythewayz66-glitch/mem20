import importlib
MOD="mem20ethicalincentivesimulatorz"
def _m(): return importlib.import_module(MOD+".domain")
def test_incentive(): m=_m(); assert m.incentive(10,5)>=0
def test_fairness(): m=_m(); assert 0<=m.fairness_score([1,2,3])<=1
def test_align(): m=_m(); assert m.align_reward({"reward":10},0.5)==5.0
def test_sim(): m=_m(); r=m.simulate_incentives([{"value":5,"effort":3}],3); assert len(r)==3
def test_violation(): m=_m(); assert m.ethical_violation({"harm":1}) is True
