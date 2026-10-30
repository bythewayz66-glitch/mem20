"""Hardware marketplace: listings, search, pricing, transactions."""
import math


def list_hardware(seller, hw, price):
    return {"seller": seller, "hardware": hw, "price": price, "available": True, "rating": 5.0}


def search(listings, query):
    q = query.lower()
    return [l for l in listings if q in l.get("hardware", "").lower() or q in l.get("seller", "").lower()]


def price_estimate(hw):
    base = hw.get("cores", 1) * 50 + hw.get("memory_gb", 1) * 10 + hw.get("storage_gb", 0) * 0.1
    if hw.get("gpu"):
        base += 200
    return round(base, 2)


def transaction(listing, buyer):
    return {"listing": listing, "buyer": buyer, "amount": listing.get("price", 0), "status": "completed"}


def marketplace_health(listings):
    if not listings:
        return {"total": 0, "available": 0, "avg_price": 0}
    avail = [l for l in listings if l.get("available")]
    prices = [l.get("price", 0) for l in avail]
    return {"total": len(listings), "available": len(avail), "avg_price": round(sum(prices) / max(1, len(prices)), 2)}
