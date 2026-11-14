import importlib
MOD="mem20globalcapabilitymarketplacez"
def _m(): return importlib.import_module(MOD+".domain")
def test_list(): m=_m(); r=m.list_capability("s","cap",10); assert r["available"] is True
def test_search(): m=_m(); ls=[m.list_capability("s","cap",10)]; r=m.search_marketplace(ls,"cap"); assert len(r)==1
def test_match(): m=_m(); ls=[m.list_capability("s","cap",10)]; r=m.match(ls,{"capability":"cap"}); assert r is not None
def test_txn(): m=_m(); l=m.list_capability("s","cap",10); r=m.transaction(l,"buyer"); assert r["status"]=="completed"
def test_health(): m=_m(); ls=[m.list_capability("s","cap",10)]; r=m.marketplace_health(ls); assert r["total"]==1
