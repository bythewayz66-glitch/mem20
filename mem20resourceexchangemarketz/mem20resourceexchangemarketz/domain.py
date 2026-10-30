"""Resource exchange market: trade resources between agents."""
import time


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
