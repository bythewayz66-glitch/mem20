"""Deterministic configuration graph: nodes, edges, resolution, validation, with estate report."""
from __future__ import annotations
import hashlib
from . import ecosystem
__all__=["add_node","add_edge","resolve","validate","diff_configs","config_report","probe","estate_context"]

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
    visited = set(); stack = set()
    def dfs(n):
        if n in stack: return False
        if n in visited: return True
        stack.add(n)
        for src, dst in graph.get("edges", []):
            if src == n and not dfs(dst): return False
        stack.discard(n); visited.add(n); return True
    for nid in graph.get("nodes", {}):
        if not dfs(nid): return {"valid": False, "reason": "cycle detected"}
    return {"valid": True, "nodes": len(graph.get("nodes", {})), "edges": len(graph.get("edges", []))}

def diff_configs(a, b):
    keys = set(a) | set(b)
    return {k: (a.get(k), b.get(k)) for k in keys if a.get(k) != b.get(k)}

def config_report(graph=None):
    graph = graph or {}
    if not graph.get("nodes"):
        add_node(graph,"base",{"region":"us","retries":3}); add_node(graph,"app",{"retries":5,"feature":True}); add_edge(graph,"base","app")
    val=validate(graph); resolved=resolve(graph,"app") or {}; diff=diff_configs({"retries":3},{"retries":5})
    peers={
        "config_events": ecosystem.config_events("config.report", {"valid":val.get("valid"),"nodes":val.get("nodes",len(graph.get("nodes",{})))}),
        "rollout_containment": ecosystem.rollout_containment("app"),
        "healing_plans": ecosystem.healing_plans(["validate","resolve","rollback"] if not val.get("valid") else ["monitor"]),
        "config_health": ecosystem.config_health(["resolver","validator"]),
        "node_distribution": ecosystem.node_distribution(["n1","n2"]),
        "config_routing": ecosystem.config_routing("app", ["resolve","validate","diff"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and val.get("valid",False),"validation":val,"resolved_keys":len(resolved),"diff_keys":len(diff),"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=config_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":all(v.get("ok") for v in r.get("peers",{}).values()),"checks":r.get("peers",{})}
