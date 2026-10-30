import importlib
MOD="mem20resourceexchangemarketz"
def _m(): return importlib.import_module(MOD+".domain")
def test_list(): m=_m(); r=m.list_resource("s","cpu",10,5); assert r["available"] is True
def test_buy(): m=_m(); r=m.list_resource("s","cpu",10,5); res=m.buy(r,"b",3); assert res["ok"] is True
def test_price(): m=_m(); r=m.list_resource("s","cpu",10,5); m.buy(r,"b",3); assert r["amount"]==7
def test_health(): m=_m(); r=m.market_health([m.list_resource("s","cpu",10,5)]); assert r["listings"]==1
