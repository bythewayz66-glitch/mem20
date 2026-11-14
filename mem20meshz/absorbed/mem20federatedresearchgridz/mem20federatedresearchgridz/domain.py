"""Federated research grid: independent node contexts, local data isolation,
provenance, aggregation (numeric and conflicting/non-numeric), and
failure/idempotency/recovery semantics.

Legacy API preserved:
  register_node(grid,node), distribute_task(grid,task), aggregate_results(results),
  grid_health(grid), federated_round(grid,task)
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


def _stable_id(prefix: str, obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))
    return f"{prefix}-{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


def register_node(grid, node):
    grid = grid if isinstance(grid, dict) else {"nodes": []}
    grid.setdefault("nodes", [])
    node = dict(node or {})
    nid = str(node.get("id") or node.get("node_id") or f"node-{len(grid['nodes'])+1}")
    node["id"] = nid
    node.setdefault("status", "ready")
    node.setdefault("load", 0)
    node.setdefault("compute", 1)
    node.setdefault("local_data", {})  # isolated to this node
    node.setdefault("processed_task_ids", [])
    if not any(n.get("id") == nid for n in grid["nodes"]):
        grid["nodes"].append(node)
    return grid


def distribute_task(grid, task, strategy="least_loaded"):
    ready = [n for n in (grid or {}).get("nodes", []) if n.get("status") == "ready"]
    if not ready:
        return None
    if strategy == "broadcast":
        return list(ready)
    best = min(ready, key=lambda n: (float(n.get("load", 0)), str(n.get("id"))))
    best["load"] = float(best.get("load", 0)) + float((task or {}).get("cost", 1))
    return best


def _validate_result(result: Mapping[str, Any]) -> Dict[str, Any]:
    issues = []
    if not isinstance(result, Mapping):
        return {"valid": False, "issues": ["result_not_mapping"]}
    if not result.get("node_id"):
        issues.append("missing_node_id")
    if not result.get("task_id"):
        issues.append("missing_task_id")
    if "value" not in result and "output" not in result:
        issues.append("missing_value_or_output")
    prov = result.get("provenance") or {}
    if not isinstance(prov, Mapping) or not prov.get("local_data_keys"):
        issues.append("missing_provenance")
    return {"valid": len(issues) == 0, "issues": issues}


def _local_compute(node: Mapping[str, Any], task: Mapping[str, Any]) -> Any:
    """Compute using only node-local data; never reads other nodes' local_data."""
    local = dict(node.get("local_data") or {})
    query = str(task.get("query") or task.get("type") or "")
    records = list(local.get("records") or [])
    # legacy compatibility: simple compute*size when no local records/research query
    if not records and not query:
        return float(node.get("compute", 1) or 1) * float(task.get("size", task.get("cost", 1)) or 1)
    tokens = [t for t in "".join(ch.lower() if ch.isalnum() else " " for ch in query).split() if t]
    matched = []
    for r in records:
        text = json.dumps(r, sort_keys=True, default=str).lower()
        if not tokens or any(t in text for t in tokens):
            matched.append(r)
    numeric_vals = []
    labels = []
    label_keys = {"label", "class", "answer", "verdict", "finding", "result", "category"}
    for r in matched:
        if isinstance(r, (int, float)) and not isinstance(r, bool):
            numeric_vals.append(float(r))
        elif isinstance(r, Mapping):
            for k, v in r.items():
                lk = str(k).lower()
                if lk in label_keys:
                    labels.append(str(v))
                elif isinstance(v, (int, float)) and not isinstance(v, bool):
                    numeric_vals.append(float(v))
        elif r is not None:
            labels.append(str(r))
    if labels:
        return Counter(labels).most_common(1)[0][0]
    if numeric_vals:
        return round(sum(numeric_vals) * float(node.get("compute", 1) or 1), 6)
    if not records and (task.get("size") is not None or task.get("compute") is not None):
        return round(float(node.get("compute", 1) or 1) * float(task.get("size", task.get("cost", 1)) or 1), 6)
    return {"matched": len(matched), "node": node.get("id"), "query": query}


def execute_task_on_node(node: Dict[str, Any], task: Mapping[str, Any], task_id: Optional[str] = None, delivery_id: Optional[str] = None) -> Dict[str, Any]:
    task_id = str(task_id or task.get("task_id") or _stable_id("task", task))
    delivery_id = str(delivery_id or task.get("delivery_id") or uuid.uuid4().hex)
    processed = node.setdefault("processed_task_ids", [])
    # duplicate delivery/idempotency: if same task_id already completed, return cached result
    cache = node.setdefault("result_cache", {})
    if task_id in cache:
        cached = dict(cache[task_id])
        cached["duplicate_delivery"] = True
        cached["delivery_id"] = delivery_id
        cached["idempotent_replay"] = True
        return cached
    if node.get("status") not in ("ready", "busy"):
        raise RuntimeError(f"node {node.get('id')} unavailable: {node.get('status')}")
    value = _local_compute(node, task)
    result = {
        "ok": True,
        "node": node.get("id"),  # legacy alias
        "node_id": node.get("id"),
        "task_id": task_id,
        "delivery_id": delivery_id,
        "value": value,
        "output": {"value": value},
        "provenance": {
            "node_id": node.get("id"),
            "task_id": task_id,
            "local_data_keys": sorted(list((node.get("local_data") or {}).keys())),
            "local_record_count": len(((node.get("local_data") or {}).get("records") or [])),
            "computed_at": time.time(),
            "algorithm": "local_compute_v1",
        },
        "validation": None,
        "duplicate_delivery": False,
    }
    result["validation"] = _validate_result(result)
    processed.append(task_id)
    cache[task_id] = dict(result)
    return result


def aggregate_results(results):
    """Legacy-compatible aggregation plus non-numeric/conflict semantics."""
    results = list(results or [])
    if not results:
        return {}
    # normalize: allow raw numeric list or dict results
    normalized = []
    for r in results:
        if isinstance(r, Mapping) and "value" in r:
            normalized.append(r.get("value"))
        elif isinstance(r, Mapping) and "output" in r and isinstance(r["output"], Mapping) and "value" in r["output"]:
            normalized.append(r["output"]["value"])
        else:
            normalized.append(r)
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in normalized):
        return round(sum(float(v) for v in normalized) / len(normalized), 4)
    # dict numeric-field average legacy behavior
    if all(isinstance(v, Mapping) for v in normalized):
        out = {}
        keys = set()
        for r in normalized:
            keys.update(r.keys())
        for k in keys:
            vals = [r.get(k) for r in normalized if isinstance(r.get(k), (int, float)) and not isinstance(r.get(k), bool)]
            if vals:
                out[k] = round(sum(float(v) for v in vals) / len(vals), 4)
        if out:
            return out
    # non-numeric/conflicting outputs
    counts = Counter(json.dumps(v, sort_keys=True, default=str) if isinstance(v, (dict, list)) else str(v) for v in normalized)
    total = len(normalized)
    dist = []
    for raw, n in counts.most_common():
        try:
            val = json.loads(raw)
        except Exception:
            val = raw
        dist.append({"value": val, "count": n, "share": round(n / total, 4)})
    majority = dist[0]
    return {
        "type": "categorical_aggregate",
        "total": total,
        "majority": majority["value"],
        "majority_share": majority["share"],
        "consensus": majority["share"] == 1.0,
        "conflict": majority["share"] < 1.0,
        "distribution": dist,
    }


def grid_health(grid):
    nodes = (grid or {}).get("nodes", []) or []
    if not nodes:
        return {"total": 0, "ready": 0, "health": 0.0}
    ready = sum(1 for n in nodes if n.get("status") == "ready")
    return {"total": len(nodes), "ready": ready, "health": round(ready / len(nodes), 4)}


def federated_round(grid, task, max_retries=1):
    """Legacy-compatible single-node round; enhanced to handle node loss/retry."""
    task = dict(task or {})
    task_id = str(task.get("task_id") or _stable_id("task", task))
    task["task_id"] = task_id
    attempts = 0
    last_err = None
    while attempts <= max(0, int(max_retries)):
        attempts += 1
        node = distribute_task(grid, task)
        if not node or (isinstance(node, list) and not node):
            last_err = "no_ready_node"
            break
        if isinstance(node, list):
            node = node[0]
        try:
            if node.get("status") == "lost":
                raise RuntimeError("node lost")
            result = execute_task_on_node(node, task, task_id=task_id)
            return {"ok": True, "result": result, "task_id": task_id, "attempts": attempts, "node_id": node.get("id")}
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            node["status"] = "ready"  # allow retry scheduling
    return {"ok": False, "error": last_err, "task_id": task_id, "attempts": attempts, "partial_results": []}


def federated_research_round(grid, task, min_nodes=2, max_retries=1, require_local_data=False):
    """Execute a research task across >=min_nodes independent node contexts with local data isolation."""
    task = dict(task or {})
    task_id = str(task.get("task_id") or _stable_id("task", task))
    task["task_id"] = task_id
    nodes = [n for n in (grid or {}).get("nodes", []) if n.get("status") == "ready"]
    if require_local_data:
        nodes = [n for n in nodes if ((n.get("local_data") or {}).get("records") is not None)]
    selected = nodes[: max(1, int(min_nodes))]
    if len(selected) < max(1, int(min_nodes)):
        return {"ok": False, "task_id": task_id, "error": "insufficient_ready_nodes", "available": len(selected), "required": min_nodes, "partial_results": []}
    results = []
    errors = []
    for node in selected:
        attempts = 0
        done = False
        while attempts <= max(0, int(max_retries)) and not done:
            attempts += 1
            try:
                if node.get("status") == "lost":
                    raise RuntimeError("node lost")
                # local boundary: each node computes only from its own local_data
                r = execute_task_on_node(node, task, task_id=task_id, delivery_id=f"{task_id}:{node.get('id')}:{attempts}")
                r["attempts"] = attempts
                results.append(r)
                done = True
            except Exception as e:
                if attempts > max_retries:
                    errors.append({"node_id": node.get("id"), "error": f"{type(e).__name__}: {e}", "attempts": attempts})
                else:
                    time.sleep(0)
    valid = [r for r in results if (r.get("validation") or {}).get("valid", True)]
    aggregate = aggregate_results(valid)
    return {
        "ok": len(valid) >= 1 and len(errors) == 0,
        "task_id": task_id,
        "nodes_selected": [n.get("id") for n in selected],
        "results": results,
        "valid_results": len(valid),
        "errors": errors,
        "aggregate": aggregate,
        "local_data_isolated": True,
        "provenance_complete": all(bool(r.get("provenance")) for r in results),
        "partial_result_recovery": len(results) > 0 and len(errors) > 0,
    }
