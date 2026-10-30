import importlib
MOD="mem20gamebalancesimulatorz"
def _m(): return importlib.import_module(MOD+".domain")
def test_dps(): m=_m(); assert m.dps(10,2)==20
def test_ttk(): m=_m(); assert m.ttk(100,10)==10.0
def test_econ(): m=_m(); assert m.economy_balance(100,40)==60
def test_curve(): m=_m(); r=m.difficulty_curve(3); assert len(r)==3
def test_win(): m=_m(); assert m.win_rate([{"winner":"player"},{"winner":"enemy"}])==0.5
