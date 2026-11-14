"""Global capability marketplace: listings, search, matching, transactions."""
import math


def list_capability(seller, cap, price):
    return {"seller": seller, "capability": cap, "price": price, "available": True, "rating": 5.0}


def search_marketplace(listings, query):
    q = query.lower()
    return [l for l in listings if q in l.get("capability", "").lower() or q in l.get("seller", "").lower()]


def match(listings, requirement):
    candidates = [l for l in listings if l.get("available") and requirement.get("capability") in l.get("capability", "")]
    if not candidates:
        return None
    return min(candidates, key=lambda l: l.get("price", float("inf")))


def transaction(listing, buyer):
    return {"listing": listing, "buyer": buyer, "amount": listing.get("price", 0), "status": "completed"}


def marketplace_health(listings):
    if not listings:
        return {"total": 0, "available": 0, "avg_price": 0}
    avail = [l for l in listings if l.get("available")]
    prices = [l.get("price", 0) for l in avail]
    return {"total": len(listings), "available": len(avail), "avg_price": round(sum(prices) / max(1, len(prices)), 2)}
