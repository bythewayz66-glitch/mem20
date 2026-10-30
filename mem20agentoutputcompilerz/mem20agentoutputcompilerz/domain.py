"""Agent output compiler: merge, dedupe, format, and validate agent outputs."""
import json, hashlib


def merge_outputs(outputs):
    """Merge multiple agent outputs into one, preserving provenance."""
    merged = {"items": [], "sources": []}
    for o in outputs:
        merged["sources"].append(o.get("agent", "unknown"))
        for item in o.get("items", []):
            if isinstance(item, dict):
                item = dict(item)
                item["_source"] = o.get("agent", "unknown")
            else:
                item = {"value": item, "_source": o.get("agent", "unknown")}
            merged["items"].append(item)
    return merged


def dedupe(items, key="id"):
    """Dedupe items by key, keeping first occurrence."""
    seen = set()
    out = []
    for it in items:
        k = it.get(key) if isinstance(it, dict) else it
        if k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out


def compile_report(outputs, format="json"):
    """Compile agent outputs into a final report."""
    merged = merge_outputs(outputs)
    merged["items"] = dedupe(merged["items"])
    merged["count"] = len(merged["items"])
    merged["format"] = format
    merged["checksum"] = hashlib.sha256(json.dumps(merged["items"], sort_keys=True).encode()).hexdigest()[:16]
    return merged


def validate_output(output, schema=None):
    """Validate an output has required fields."""
    schema = schema or {"required": ["items"]}
    required = schema.get("required", [])
    missing = [f for f in required if f not in output]
    return {"valid": not missing, "missing": missing}


def summarize(outputs):
    """Produce a summary of agent outputs."""
    return {
        "agents": [o.get("agent") for o in outputs],
        "total_items": sum(len(o.get("items", [])) for o in outputs),
        "unique_sources": len({o.get("agent") for o in outputs}),
    }
