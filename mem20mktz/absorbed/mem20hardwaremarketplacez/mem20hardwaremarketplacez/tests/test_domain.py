import importlib
MOD="mem20hardwaremarketplacez"
def _m(): return importlib.import_module(MOD+".domain")
def test_list(): m=_m(); r=m.list_hardware("s","gpu",100); assert r["available"] is True
def test_search(): m=_m(); ls=[m.list_hardware("s","gpu",100)]; r=m.search(ls,"gpu"); assert len(r)==1
def test_price(): m=_m(); r=m.price_estimate({"cores":4,"memory_gb":16,"storage_gb":500,"gpu":True}); assert r>200
def test_txn(): m=_m(); l=m.list_hardware("s","gpu",100); r=m.transaction(l,"b"); assert r["status"]=="completed"
def test_health(): m=_m(); ls=[m.list_hardware("s","gpu",100)]; r=m.marketplace_health(ls); assert r["total"]==1
