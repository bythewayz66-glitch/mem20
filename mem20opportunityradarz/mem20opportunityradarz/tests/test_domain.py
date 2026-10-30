import importlib
MOD="mem20opportunityradarz"
def _m(): return importlib.import_module(MOD+".domain")
def test_scan(): m=_m(); r=m.scan([{"score":0.3},{"score":0.8}],0.5); assert len(r)==1
def test_score(): m=_m(); r=m.score_opportunity({"value":10,"probability":0.5},{"urgency":2}); assert r==10.0
def test_rank(): m=_m(); r=m.rank([{"value":5,"probability":0.5},{"value":10,"probability":0.5}],{}); assert r[0]["value"]==10
def test_alert(): m=_m(); r=m.alert([{"score":0.8},{"score":0.4}],0.7); assert len(r)==1
def test_health(): m=_m(); r=m.radar_health([{"score":0.8}]); assert r["high"]==1
