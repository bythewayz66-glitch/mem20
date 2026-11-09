"""Architecture simulation sandbox: load testing, topology, scaling."""
import math, random


def simulate_load(topology, rps, duration_s=60):
    """Simulate load on a topology; return per-node metrics."""
    results = []
    for node in topology.get("nodes", []):
        cap = node.get("capacity_rps", 100)
        util = min(1.0, rps / max(1, cap * node.get("count", 1)))
        latency = node.get("base_latency_ms", 10) * (1 + util * 2)
        results.append({"id": node.get("id"), "utilization": round(util, 4), "latency_ms": round(latency, 2), "overloaded": util >= 0.9})
    return results


def scaling_recommendation(metrics, target_util=0.7):
    """Recommend scaling based on metrics."""
    recs = []
    for m in metrics:
        if m["utilization"] > target_util:
            factor = math.ceil(m["utilization"] / target_util)
            recs.append({"id": m["id"], "action": "scale_up", "factor": factor})
        elif m["utilization"] < 0.2:
            recs.append({"id": m["id"], "action": "scale_down", "factor": 1})
        else:
            recs.append({"id": m["id"], "action": "none", "factor": 1})
    return recs


def topology_cost(topology, cost_per_node=0.05):
    """Estimate hourly cost of topology."""
    total_nodes = sum(n.get("count", 1) for n in topology.get("nodes", []))
    return round(total_nodes * cost_per_node, 4)


def bottleneck_node(metrics):
    """Find the bottleneck node."""
    if not metrics:
        return None
    return max(metrics, key=lambda m: m["utilization"])


def chaos_test(topology, failure_rate=0.1, seed=0):
    """Simulate random node failures."""
    rng = random.Random(seed)
    failed = []
    for node in topology.get("nodes", []):
        if rng.random() < failure_rate:
            failed.append(node.get("id"))
    return {"failed_nodes": failed, "surviving": len(topology.get("nodes", [])) - len(failed)}
