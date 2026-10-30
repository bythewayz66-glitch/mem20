"""Edge transport fabric: routing, QoS, bandwidth allocation."""
import math


def route_path(src, dst, nodes):
    # simple: direct if exists else via hub
    if dst in nodes.get(src, []):
        return [src, dst]
    # find hub
    for hub in nodes:
        if dst in nodes.get(hub, []) and src in nodes.get(hub, []):
            return [src, hub, dst]
    return [src, dst]


def qos_class(latency_ms, priority):
    if priority >= 2 or latency_ms < 20:
        return "premium"
    if latency_ms < 100:
        return "standard"
    return "best_effort"


def allocate_bandwidth(total, demands):
    # proportional
    total_demand = sum(d.get("demand", 0) for d in demands) or 1
    out = []
    for d in demands:
        share = total * d.get("demand", 0) / total_demand
        out.append({"id": d.get("id"), "allocated": round(share, 2)})
    return out


def transport_health(links):
    up = sum(1 for l in links if l.get("status") == "up")
    return {"total": len(links), "up": up, "health": round(up / max(1, len(links)), 4)}
