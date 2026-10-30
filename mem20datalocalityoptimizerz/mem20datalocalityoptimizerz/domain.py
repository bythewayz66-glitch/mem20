"""Data locality optimizer: placement, migration, cost."""
import math


def placement_score(node, data):
    latency = node.get("latency_ms", 10)
    cost = node.get("cost_per_gb", 0.05)
    capacity = node.get("capacity_gb", 100)
    used = node.get("used_gb", 0)
    free = capacity - used
    if free < data.get("size_gb", 0):
        return -1
    return round(1.0 / (latency + 1) - cost * 0.5, 4)


def optimal_placement(data, nodes):
    scored = [(placement_score(n, data), n) for n in nodes]
    scored = [s for s in scored if s[0] >= 0]
    if not scored:
        return None
    scored.sort(reverse=True)
    return scored[0][1]


def migration_cost(data, src, dst):
    size = data.get("size_gb", 0)
    egress = src.get("egress_cost", 0.09)
    return round(size * egress, 4)


def locality_report(placements):
    total = len(placements)
    local = sum(1 for p in placements if p.get("local"))
    return {"total": total, "local": local, "ratio": round(local / max(1, total), 4)}


def rebalance(nodes, data_items):
    # assign each data item to best node
    assignments = {}
    for d in data_items:
        n = optimal_placement(d, nodes)
        if n:
            assignments[d.get("id")] = n.get("id")
            n["used_gb"] = n.get("used_gb", 0) + d.get("size_gb", 0)
    return assignments
