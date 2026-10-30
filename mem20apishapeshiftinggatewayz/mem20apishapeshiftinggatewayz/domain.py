"""API shape-shifting gateway: schema adaptation, versioning, transformation."""
import json, hashlib


def transform_payload(payload, mapping):
    """Transform payload fields according to mapping dict (old->new)."""
    out = {}
    for k, v in payload.items():
        new_key = mapping.get(k, k)
        out[new_key] = v
    return out


def version_route(path, version):
    """Build versioned route path."""
    return f"/v{version}{path}" if not path.startswith(f"/v{version}") else path


def schema_diff(old_schema, new_schema):
    """Compute added/removed/changed fields between schemas."""
    old_keys = set(old_schema.get("properties", {}).keys())
    new_keys = set(new_schema.get("properties", {}).keys())
    return {
        "added": sorted(new_keys - old_keys),
        "removed": sorted(old_keys - new_keys),
        "common": sorted(old_keys & new_keys),
    }


def adapt_response(response, target_version):
    """Adapt a response to a target API version."""
    r = dict(response)
    r["_version"] = target_version
    return r


def gateway_hash(route, method, body):
    return hashlib.sha256(f"{method}:{route}:{body}".encode()).hexdigest()[:16]


def rate_limit_key(ip, route):
    return f"{ip}:{route}"
