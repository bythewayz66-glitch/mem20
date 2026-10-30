"""Edge-to-cloud intelligence continuum: tiering, offload, sync."""
import math


def tier_for_latency(latency_ms):
    if latency_ms < 10:
        return "edge"
    if latency_ms < 100:
        return "fog"
    return "cloud"


def offload_decision(task, edge_cap, cloud_cap):
    if task.get("size", 0) <= edge_cap and task.get("latency_req", 1000) < 50:
        return "edge"
    if task.get("size", 0) <= cloud_cap:
        return "cloud"
    return "reject"


def sync_state(edge_state, cloud_state):
    merged = dict(cloud_state)
    merged.update(edge_state)
    return merged


def bandwidth_cost(size_mb, rate_per_mb=0.01):
    return round(size_mb * rate_per_mb, 4)


def continuum_health(edge_nodes, cloud):
    edge_ok = sum(1 for n in edge_nodes if n.get("status") == "online")
    return {"edge_online": edge_ok, "edge_total": len(edge_nodes), "cloud_status": cloud.get("status", "unknown")}
