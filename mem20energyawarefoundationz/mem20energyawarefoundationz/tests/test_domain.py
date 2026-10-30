import importlib
MOD="mem20energyawarefoundationz"
def _m(): return importlib.import_module(MOD+".domain")
def test_reading(): m=_m(); r=m.power_reading({"id":"d1","power_watts":50,"ts":1}); assert r["watts"]==50
def test_threshold(): m=_m(); r=m.threshold_check({"watts":150},100); assert r["exceeded"] is True
def test_budget(): m=_m(); r=m.energy_budget([{"power_watts":50},{"power_watts":60}],200); assert r["within_budget"] is True
def test_optimize(): m=_m(); r=m.optimize_power([{"id":"d1","power_watts":100}],0.1); assert len(r)==1
def test_daily(): m=_m(); assert m.daily_energy([{"power_watts":100}],24)==2.4
