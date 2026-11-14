"""Compounding product ecosystem: synergies, network effects, growth, with estate report."""
from __future__ import annotations
import math
from . import ecosystem
__all__=["synergy","network_value","compound_growth","ecosystem_health","cross_sell_matrix","ecosystem_report","probe","estate_context"]

def synergy(a, b):
    shared = set(a.get("users", [])) & set(b.get("users", []))
    return round(len(shared) * 0.1 + a.get("value", 0) * b.get("value", 0) * 0.01, 4)

def network_value(n_users, connections_per_user=3):
    _=connections_per_user
    return round(n_users * (n_users - 1) / 2 * 0.01, 2)

def compound_growth(initial, rate, periods):
    out = [initial]; cur = initial
    for _ in range(max(0,periods - 1)): cur = cur * (1 + rate); out.append(round(cur, 2))
    return out

def ecosystem_health(products):
    if not products: return 0.0
    pairs=max(1, len(products) * (len(products) - 1) / 2)
    avg_synergy = sum(synergy(products[i], products[j]) for i in range(len(products)) for j in range(i + 1, len(products))) / pairs
    return round(min(1.0, avg_synergy + 0.3), 4)

def cross_sell_matrix(products):
    matrix = {}
    for a in products:
        for b in products:
            if a.get("id") != b.get("id"): matrix.setdefault(a.get("id"), {})[b.get("id")] = synergy(a, b)
    return matrix

def ecosystem_report(products=None, initial=100.0, rate=0.1, periods=4):
    products = products or [{"id":"a","value":1,"users":["u1","u2"]},{"id":"b","value":2,"users":["u2","u3"]}]
    health=ecosystem_health(products); nv=network_value(50); growth=compound_growth(initial,rate,periods); matrix=cross_sell_matrix(products)
    peers={
        "loyalty_graph": ecosystem.loyalty_graph([p["id"] for p in products]),
        "lifecycle_value": ecosystem.lifecycle_value(),
        "growth_economics": ecosystem.growth_economics(initial,rate,periods),
        "pipeline_signal": ecosystem.pipeline_signal(growth[-1] if growth else initial),
        "demand_signal": ecosystem.demand_signal([initial*(1+rate)**i for i in range(min(5,periods+1))]),
        "partnership_synergy": ecosystem.partnership_synergy(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"ecosystem_health":health,"network_value":nv,"growth":growth,"cross_sell_edges":sum(len(v) for v in matrix.values()),"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=ecosystem_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
