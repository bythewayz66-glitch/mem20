import importlib
MOD="mem20offerassemblyfabricz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_offer([{"price":5}],10); assert r["status"]=="draft"
def test_add(): m=_m(); r=m.create_offer([],0); m.add_component(r,{"price":3}); assert len(r["components"])==1
def test_price(): m=_m(); r=m.create_offer([{"price":5},{"price":3}],0); assert m.price_offer(r,"sum")==8
def test_publish(): m=_m(); r=m.create_offer([],0); m.publish(r); assert r["status"]=="published"
def test_health(): m=_m(); r=m.offer_health([m.create_offer([],0)]); assert r["total"]==1
