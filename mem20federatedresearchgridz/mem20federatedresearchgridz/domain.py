"""Federated research grid: node registration, task distribution, aggregation."""
import math, random


def register_node(grid, node):
    grid.setdefault("nodes", [])
    if not any(n.get("id") == node.get("id") for n in grid["nodes"]):
        grid["nodes"].append({**node, "status": "ready"})
    return grid


def distribute_task(grid, task):
    ready = [n for n in grid.get("nodes", []) if n.get("status") == "ready"]
    if not ready:
        return None
    # least loaded
    best = min(ready, key=lambda n: n.get("load", 0))
    best["load"] = best.get("load", 0) + task.get("cost", 1)
    return best


def aggregate_results(results):
    if not results:
        return {}
    if isinstance(results[0], (int, float)):
        return round(sum(results) / len(results), 4)
    # dict: average numeric fields
    out = {}
    keys = set()
    for r in results:
        keys.update(r.keys())
    for k in keys:
        vals = [r.get(k) for r in results if isinstance(r.get(k), (int, float))]
        if vals:
            out[k] = round(sum(vals) / len(vals), 4)
    return out


def grid_health(grid):
    nodes = grid.get("nodes", [])
    if not nodes:
        return {"total": 0, "ready": 0, "health": 0.0}
    ready = sum(1 for n in nodes if n.get("status") == "ready")
    return {"total": len(nodes), "ready": ready, "health": round(ready / len(nodes), 4)}


def federated_round(grid, task):
    node = distribute_task(grid, task)
    if not node:
        return {"ok": False}
    result = {"node": node.get("id"), "value": node.get("compute", 1) * task.get("size", 1)}
    return {"ok": True, "result": result}
