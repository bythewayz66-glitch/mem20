"""Meaningful peer integrations for Global Capability Marketplace (#318), unique in #300-#318."""
from __future__ import annotations
from typing import Any, Dict, List

def _safe(name, fn):
    try:
        return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

def assemble_offer(listing: Dict[str, Any] = None) -> Dict[str, Any]:
    """Assemble/priced offer for a marketplace listing (real offer fabric)."""
    def run():
        from mem20offerassemblyfabricz.domain import create_offer, add_component, price_offer, publish
        l = listing or {"capability": "workflow", "price": 10}
        o = create_offer([{"id": "base", "price": float(l.get("price", 10))}])
        add_component(o, {"id": "support", "price": 2})
        priced = price_offer(o)
        pub = publish(o)
        return {"priced": priced, "published": bool(pub)}
    return _safe("mem20offerassemblyfabricz", run)

def optimize_offer(listing: Dict[str, Any] = None) -> Dict[str, Any]:
    """Evolve/score listing offer genome for marketplace fit."""
    def run():
        from mem20offergenomeenginez.domain import create_genome, mutate, fitness
        l = listing or {"price": 10, "features": ["portable"]}
        g = create_genome({"price": l.get("price", 10), "features": l.get("features", [])})
        m = mutate(g, 0.1)
        f = fitness(g, {"target_price": l.get("price", 10)})
        return {"mutated": m is not None, "fitness": f}
    return _safe("mem20offergenomeenginez", run)

def synthesize_trial(capability: Dict[str, Any] = None) -> Dict[str, Any]:
    """Synthesize instant-trial scaffold for a capability/microapp."""
    def run():
        from mem20instantappsynthesisz.domain import validate_spec, scaffold
        c = capability or {"name": "trial-capability", "type": "microapp"}
        v = validate_spec(c)
        sc = scaffold(c)
        return {"valid": v, "scaffold": sc}
    return _safe("mem20instantappsynthesisz", run)

def secure_trial(capability: Dict[str, Any] = None) -> Dict[str, Any]:
    """Validate secure execution capsule for instant trials."""
    def run():
        from mem20securecomputecapsulesz.domain import create_capsule, capsule_health
        cap = create_capsule("trial = 1+1", limits={"cpu": 1})
        h = capsule_health([cap] if cap is not None else [])
        return {"capsule": cap is not None, "health": h}
    return _safe("mem20securecomputecapsulesz", run)

def optimize_listing_query(query: str = "capability") -> Dict[str, Any]:
    """Optimize listing search/query prompt for marketplace discovery."""
    def run():
        from mem20runtimepromptoptimizerz.domain import tokenize, compress, optimize
        toks = tokenize(query)
        comp = compress(query, max_tokens=20)
        opt = optimize(query, {"clarity": 0.8}, max_tokens=20)
        return {"tokens": len(toks) if isinstance(toks, list) else 0, "compressed": comp, "optimized": opt}
    return _safe("mem20runtimepromptoptimizerz", run)

def remix_variants(listing: Dict[str, Any] = None) -> Dict[str, Any]:
    """Produce capability/asset variants for marketplace listings."""
    def run():
        from mem20assetremixstudioz.domain import remix_variants, transform_asset
        asset = listing or {"id": "cap-1", "type": "workflow"}
        vars_ = remix_variants(asset, count=2)
        tr = transform_asset(asset, {"op": "tag", "value": "portable"})
        return {"variants": vars_, "transformed": tr is not None}
    return _safe("mem20assetremixstudioz", run)

def marketplace_enrich(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Compose meaningful marketplace enrichment using legacy domain + 6 peer integrations."""
    from . import domain as _dom
    listings = payload.get("listings") or []
    requirement = payload.get("requirement") or {}
    query = str(payload.get("query") or requirement.get("capability") or "capability")
    buyer = payload.get("buyer") or "buyer"

    # legacy domain operations (real, preserved)
    health = _dom.marketplace_health(listings)
    search = _dom.search_marketplace(listings, query) if listings else []
    matched = _dom.match(listings, requirement) if listings and requirement else None
    tx = _dom.transaction(matched, buyer) if matched else None

    listing_ctx = matched or (listings[0] if listings else {"capability": query, "price": 10})
    offer = assemble_offer(listing_ctx)
    opt = optimize_offer(listing_ctx)
    trial = synthesize_trial({"name": listing_ctx.get("capability", query), "type": "microapp"})
    secure = secure_trial(listing_ctx)
    qopt = optimize_listing_query(query)
    variants = remix_variants(listing_ctx)

    integrations = {
        "assemble_offer": offer, "optimize_offer": opt, "synthesize_trial": trial,
        "secure_trial": secure, "optimize_listing_query": qopt, "remix_variants": variants,
    }
    ok = sum(1 for v in integrations.values() if v.get("ok"))
    # meaningful composition: transaction is trial-ready when secure+trial scaffolds ok
    trial_ready = bool(trial.get("ok") and secure.get("ok") and isinstance(trial.get("valid"), dict) and trial["valid"].get("valid", False))
    if tx and isinstance(tx, dict):
        tx = {**tx, "trial_ready": trial_ready, "offer_published": bool(offer.get("ok") and offer.get("published"))}
    return {
        "marketplace_health": health, "search_results": search, "match": matched, "transaction": tx,
        "trial_ready": trial_ready, "integration_health": {"ok": ok, "total": 6},
        "integrations": integrations,
    }

def probe() -> Dict[str, Any]:
    checks = {
        "assemble_offer": assemble_offer(), "optimize_offer": optimize_offer(),
        "synthesize_trial": synthesize_trial(), "secure_trial": secure_trial(),
        "optimize_listing_query": optimize_listing_query(), "remix_variants": remix_variants(),
    }
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}
