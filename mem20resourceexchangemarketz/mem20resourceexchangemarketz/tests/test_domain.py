import importlib
MOD="mem20resourceexchangemarketz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")
def test_list(): l=_m().list_resource("s","r",5,1); assert l["available"]
def test_buy(): l=_m().list_resource("s","r",5,2); r=_m().buy(l,"b",2); assert r["ok"] and r["cost"]==4
def test_buy_insufficient(): l=_m().list_resource("s","r",1,1); assert not _m().buy(l,"b",5)["ok"]
def test_health(): h=_m().market_health([{"available":True},{"available":False}]); assert h["available"]==1
def test_eco_route(): r=_eco().market_routing("k",["t"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"
def test_eco_events(): r=_eco().trade_events("t",{}); assert r["ok"] and r["subsystem"]=="mem20eventstreamsuperhighwayz"
def test_eco_contain(): r=_eco().trade_containment("t"); assert r["ok"] and r["subsystem"]=="mem20faultcontainmentcellsz"
def test_eco_price(): r=_eco().demand_pricing([1,2]); assert r["ok"] and r["subsystem"]=="mem20demandforecastandcapacitybrainz"
def test_eco_econ(): r=_eco().trade_economics(10,4); assert r["ok"] and r["subsystem"]=="mem20simz"
def test_eco_loyalty(): r=_eco().participant_loyalty(["a","b"]); assert r["ok"] and r["subsystem"]=="mem20crossproductloyaltygraphz"
def test_report_and_probe():
    m=_m(); rep=m.market_report(); assert rep["trade_cost"]==6.0 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
