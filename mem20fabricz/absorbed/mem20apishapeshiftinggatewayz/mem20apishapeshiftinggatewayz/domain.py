"""API shape-shifting gateway: schema adaptation, versioning, transformation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from memory_engine import EngineConfig, MemoryEngine
from toolchest.catalog import load_inventory
import mem20path
from mem20webhooksupernetworkz.domain import DeliveryLedger
from mem20mixedinitiativefocusenginez.domain import focus_score


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


def _toolchest_inventory_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    p = root / "toolchest" / "inventory.json"
    return p if p.exists() else root / "toolchest" / "src" / "toolchest" / "inventory.json"


def estate_context(store_path: str | Path | None = None) -> dict:
    scripts = mem20path.discover_scripts()
    inv = load_inventory(_toolchest_inventory_path())
    ledger = DeliveryLedger(max_entries=4)
    ledger.add("asg-probe")
    score = focus_score({"priority": 1, "distractions": 0})
    ctx = {
        "path_scripts": len(scripts) if isinstance(scripts, dict) else 0,
        "toolchest_total": int(inv.get("total", 0)) if isinstance(inv, dict) else 0,
        "dedup_probe_seen": "asg-probe" in ledger,
        "focus_probe": float(score),
    }
    if store_path is not None:
        cfg = EngineConfig(store_path=Path(store_path).expanduser().resolve())
        eng = MemoryEngine(cfg)
        _ = eng.config
        ctx["engine_status_checked"] = True
    return ctx
