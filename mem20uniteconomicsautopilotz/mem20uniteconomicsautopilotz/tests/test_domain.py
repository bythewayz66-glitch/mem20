import importlib
MOD="mem20uniteconomicsautopilotz"
def _m(): return importlib.import_module(MOD+".domain")
def test_ltv(): m=_m(); r=m.ltv(10,0.1); assert r==100.0
def test_cac(): m=_m(); r=m.cac(100,5); assert r==20.0
def test_pay(): m=_m(); r=m.payback_months(20,10); assert r==2.0
def test_ratio(): m=_m(); r=m.ltv_cac_ratio(100,20); assert r==5.0
def test_health(): m=_m(); r=m.economics_health({"ltv":100,"cac":20,"ratio":5}); assert "ratio" in r
