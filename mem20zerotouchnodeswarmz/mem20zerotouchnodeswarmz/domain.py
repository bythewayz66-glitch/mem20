"""Zero-touch node swarm: discovery, joining, task distribution, healing.

Real domain logic: nodes register themselves, the swarm discovers them,
assigns work by capacity, and heals around failures without manual ops.
"""
import math, time


def register_node(swarm, node):
    """Add a node to the swarm if not present; return updated swarm."""
    nodes = list(swarm.get("nodes", []))
    ids = {n.get("id") for n in nodes}
    if node.get("id") not in ids:
        n = dict(node)
        n.setdefault("status", "ready")
        n.setdefault("load", 0.0)
        n.setdefault("joined_at", time.time())
        nodes.append(n)
    return {"nodes": nodes, "count": len(nodes)}


def discover(swarm, capability=None):
    """List ready nodes, optionally filtered by capability."""
    out = []
    for n in swarm.get("nodes", []):
        if n.get("status") != "ready":
            continue
        if capability and capability not in n.get("capabilities", []):
            continue
        out.append(n)
    return out


def node_score(node, task):
    """Score a node for a task: capacity*availability - load - latency."""
    cap = float(node.get("capacity", 1.0))
    avail = float(node.get("availability", 1.0))
    load = float(node.get("load", 0.0))
    lat = float(node.get("latency_ms", 0.0))
    energy = float(node.get("energy", 0.0))
    urgency = float(task.get("urgency", 0.5))
    return round(cap * avail * (1 + 0.2 * urgency) - load - 0.001 * lat - 0.05 * energy, 6)


def assign_task(swarm, task):
    """Pick best node for a task; return assignment + fallbacks."""
    candidates = discover(swarm, task.get("capability"))
    if not candidates:
        return {"node": None, "score": 0.0, "fallbacks": []}
    scored = sorted(((node_score(n, task), n) for n in candidates), reverse=True)
    best_score, best = scored[0]
    fallbacks = [n for _, n in scored[1:3]]
    return {"node": best, "score": best_score, "fallbacks": fallbacks}


def mark_failed(swarm, node_id):
    """Mark a node failed and re-route its load."""
    nodes = []
    failed = None
    for n in swarm.get("nodes", []):
        if n.get("id") == node_id:
            failed = dict(n)
            failed["status"] = "failed"
            nodes.append(failed)
        else:
            nodes.append(dict(n))
    return {"nodes": nodes, "failed": failed}


def heal(swarm):
    """Remove failed nodes and rebalance; return healed swarm + actions."""
    actions = []
    healthy = []
    for n in swarm.get("nodes", []):
        if n.get("status") == "failed":
            actions.append({"id": n.get("id"), "action": "evict"})
        else:
            healthy.append(dict(n))
    # rebalance load
    total = sum(float(n.get("load", 0)) for n in healthy)
    for n in healthy:
        n["load"] = round(total / max(1, len(healthy)), 3) if healthy else 0.0
    return {"nodes": healthy, "actions": actions, "healed": len(actions)}


def quorum(swarm, required=0.5):
    """Check if ready nodes meet quorum fraction."""
    ready = len(discover(swarm))
    total = len(swarm.get("nodes", []))
    if total == 0:
        return False
    return (ready / total) >= required


def load_distribution(swarm):
    """Stats on node load."""
    loads = [float(n.get("load", 0)) for n in swarm.get("nodes", []) if n.get("status") == "ready"]
    if not loads:
        return {"min": 0, "max": 0, "mean": 0, "spread": 0}
    return {"min": min(loads), "max": max(loads), "mean": sum(loads)/len(loads), "spread": max(loads)-min(loads)}


def join_token(node_id, secret="swarm"):
    """Generate a simple join token for a node."""
    import hashlib
    return hashlib.sha256(f"{secret}:{node_id}".encode()).hexdigest()[:16]
