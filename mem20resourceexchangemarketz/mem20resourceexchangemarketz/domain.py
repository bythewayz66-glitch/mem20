"""Resource exchange market: trade resources between agents, with estate report."""
from __future__ import annotations
import time
from . import ecosystem
__all__=["list_resource","buy","price_history","market_health","market_report","probe","estate_context"]

def list_resource(seller, resource, amount, price):
    return {"seller": seller, "resource": resource, "amount": amount, "price": price, "available": True}

def buy(listing, buyer, qty):
    if qty > listing["amount"]:
        return {"ok": False, "reason": "insufficient"}
    listing["amount"] -= qty
    if listing["amount"] == 0:
        listing["available"] = False
    return {"ok": True, "buyer": buyer, "qty": qty, "cost": qty*listing["price"]}

def price_history(trades):
    return [{"price": t.get("price"), "ts": t.get("ts")} for t in trades]

def market_health(listings):
    return {"listings": len(listings), "available": sum(1 for l in listings if l.get("available"))}

def market_report():
    l1=list_resource("alice","cpu",10,2.0); l2=list_resource("bob","gpu",2,5.0)
    trade=buy(l1,"carol",3); h=market_health([l1,l2])
    peers={
        "market_routing": ecosystem.market_routing("cpu", ["list","buy","price"]),
        "trade_events": ecosystem.trade_events("trade.executed", {"buyer":"carol","cost":trade.get("cost")}),
        "trade_containment": ecosystem.trade_containment("t1"),
        "demand_pricing": ecosystem.demand_pricing([2.0,2.1,2.0]),
        "trade_economics": ecosystem.trade_economics(trade.get("cost",0), 2.0),
        "participant_loyalty": ecosystem.participant_loyalty(["alice","carol"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and trade.get("ok",False),"available":h["available"],"trade_cost":trade.get("cost"),"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=market_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
