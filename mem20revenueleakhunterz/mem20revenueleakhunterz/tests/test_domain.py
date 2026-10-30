import importlib
MOD="mem20revenueleakhunterz"
def _m(): return importlib.import_module(MOD+".domain")
def test_detect(): m=_m(); r=m.detect_leaks([{"id":"t1","amount":90}],{"t1":100}); assert len(r)==1
def test_anom(): m=_m(); r=m.anomaly_score([1,2,3,100]); assert r>0
def test_rec(): m=_m(); r=m.detect_leaks([{"id":"t1","amount":90}],{"t1":100}); assert m.recoverable(r)==10
def test_health(): m=_m(); r=m.detect_leaks([{"id":"t1","amount":90}],{"t1":100}); assert m.hunter_health(r)["leaks"]==1
