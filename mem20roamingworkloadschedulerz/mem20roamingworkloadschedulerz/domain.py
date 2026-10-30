"""Roaming workload scheduler: migrate workloads across nodes."""
import time


def schedule(workloads, nodes):
    assignments = []
    for w in workloads:
        # pick node with least load
        node = min(nodes, key=lambda n: n.get("load", 0))
        node["load"] = node.get("load", 0) + w.get("cost", 1)
        assignments.append({"workload": w.get("id"), "node": node.get("id")})
    return assignments


def migrate(workload_id, from_node, to_node):
    return {"workload": workload_id, "from": from_node, "to": to_node, "migrated_at": time.time()}


def node_load(nodes):
    return {n.get("id"): n.get("load", 0) for n in nodes}


def scheduler_health(nodes):
    loads = [n.get("load", 0) for n in nodes]
    return {"nodes": len(nodes), "total_load": sum(loads), "max_load": max(loads) if loads else 0}
