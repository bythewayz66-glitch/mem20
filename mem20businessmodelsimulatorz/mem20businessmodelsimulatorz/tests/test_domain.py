import importlib
MOD="mem20businessmodelsimulatorz"
def _m(): return importlib.import_module(MOD+".domain")
def test_revenue(): m=_m(); assert m.revenue(10,5)==50
def test_cost(): m=_m(); assert m.cost(100,2,10)==120
def test_profit(): m=_m(); assert m.profit(500,300)==200
def test_break_even(): m=_m(); assert m.break_even(1000,10,4)==167
def test_scenario(): m=_m(); r=m.scenario_sim(100,10,500,2,0.1,3); assert len(r)==3
