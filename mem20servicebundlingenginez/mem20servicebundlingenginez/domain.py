"""Service bundling engine: bundle services into packages."""
import time


def create_bundle(services, name="bundle"):
    return {"name": name, "services": list(services), "price": sum(s.get("price", 0) for s in services), "created": time.time()}


def add_service(bundle, service):
    bundle["services"].append(service)
    bundle["price"] = sum(s.get("price", 0) for s in bundle["services"])
    return bundle


def discount(bundle, rate=0.1):
    bundle["price"] = round(bundle["price"] * (1 - rate), 2)
    return bundle


def bundle_health(bundles):
    return {"bundles": len(bundles), "services": sum(len(b["services"]) for b in bundles)}
