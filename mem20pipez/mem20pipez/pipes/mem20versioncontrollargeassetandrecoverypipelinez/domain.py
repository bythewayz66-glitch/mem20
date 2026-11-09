"""Version control for large assets and recovery pipeline."""
import hashlib, time


def version_asset(asset_id, content):
    h = hashlib.sha256(content.encode() if isinstance(content, str) else content).hexdigest()
    return {"asset_id": asset_id, "version": h[:8], "hash": h, "ts": time.time(), "size": len(content)}


def diff_versions(v1, v2):
    return {"asset_id": v1["asset_id"], "from": v1["version"], "to": v2["version"], "changed": v1["hash"] != v2["hash"]}


def recover(versions, target_version):
    for v in versions:
        if v["version"] == target_version:
            return v
    return None


def vc_health(versions):
    return {"versions": len(versions), "assets": len(set(v["asset_id"] for v in versions))}
