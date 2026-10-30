"""Offer assembly fabric: compose offers from components."""
import time


def create_offer(components, price=0):
    return {"id": f"offer-{int(time.time())}", "components": list(components), "price": price, "status": "draft", "created": time.time()}


def add_component(offer, component):
    offer["components"].append(component)
    return offer


def price_offer(offer, strategy="sum"):
    if strategy == "sum":
        return sum(c.get("price", 0) for c in offer["components"])
    if strategy == "max":
        return max((c.get("price", 0) for c in offer["components"]), default=0)
    return 0


def publish(offer):
    offer["status"] = "published"
    offer["published_at"] = time.time()
    return offer


def offer_health(offers):
    published = sum(1 for o in offers if o.get("status") == "published")
    return {"total": len(offers), "published": published, "draft": len(offers)-published}
