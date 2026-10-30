"""Deterministic configuration graph: nodes, edges, resolution, validation."""
import hashlib


def add_node(graph, node_id, config):
    graph.setdefault("nodes", {})[node_id] = {"id": node_id, "config": config, "hash": hashlib.sha256(str(config).encode()).hexdigest()[:8]}
    return graph


def add_edge(graph, src, dst):
    graph.setdefault("edges", []).append((src, dst))
    return graph


def resolve(graph, node_id):
    """Resolve final config by walking dependencies."""
    node = graph.get("nodes", {}).get(node_id)
    if not node:
        return None
    result = dict(node["config"])
    for src, dst in graph.get("edges", []):
        if dst == node_id:
            parent = resolve(graph, src)
            if parent:
                result = {**parent, **result}
    return result


def validate(graph):
    # check for cycles
    visited = set()
    stack = set()
    def dfs(n):
        if n in stack:
            return False
        if n in visited:
            return True
        stack.add(n)
        for src, dst in graph.get("edges", []):
            if src == n and not dfs(dst):
                return False
        stack.discard(n)
        visited.add(n)
        return True
    for nid in graph.get("nodes", {}):
        if not dfs(nid):
            return {"valid": False, "reason": "cycle detected"}
    return {"valid": True, "nodes": len(graph.get("nodes", {})), "edges": len(graph.get("edges", []))}


def diff_configs(a, b):
    keys = set(a) | set(b)
    return {k: (a.get(k), b.get(k)) for k in keys if a.get(k) != b.get(k)}
