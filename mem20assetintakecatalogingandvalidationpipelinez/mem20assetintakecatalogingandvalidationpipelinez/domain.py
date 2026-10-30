"""Asset intake, cataloging, and validation pipeline."""
import hashlib, os


def validate_asset(asset):
    """Validate an asset has required fields and valid format."""
    required = ["id", "type", "format"]
    missing = [r for r in required if r not in asset]
    valid_formats = {"image": ["png", "jpg", "webp"], "model": ["fbx", "gltf", "obj"], "audio": ["wav", "mp3", "ogg"]}
    fmt_ok = asset.get("format") in valid_formats.get(asset.get("type"), [])
    return {"valid": not missing and fmt_ok, "missing": missing, "format_ok": fmt_ok}


def catalog_asset(asset):
    """Create a catalog entry for an asset."""
    return {
        "id": asset.get("id"),
        "type": asset.get("type"),
        "format": asset.get("format"),
        "checksum": hashlib.sha256(str(asset).encode()).hexdigest()[:16],
        "size_bytes": asset.get("size_bytes", 0),
        "tags": asset.get("tags", []),
    }


def intake_pipeline(assets):
    """Run intake validation + cataloging pipeline."""
    results = []
    for a in assets:
        v = validate_asset(a)
        entry = catalog_asset(a) if v["valid"] else None
        results.append({"asset": a.get("id"), "valid": v["valid"], "catalog": entry, "errors": v["missing"] + ([] if v["format_ok"] else ["bad format"])})
    return {"processed": len(results), "valid": sum(1 for r in results if r["valid"]), "results": results}


def search_catalog(catalog, query):
    """Search catalog by tag or type."""
    q = query.lower()
    return [c for c in catalog if q in str(c.get("tags", [])).lower() or q in str(c.get("type", "")).lower() or q in str(c.get("id", "")).lower()]


def dedupe_assets(assets):
    """Dedupe assets by checksum."""
    seen = set()
    out = []
    for a in assets:
        cs = hashlib.sha256(str(a).encode()).hexdigest()[:16]
        if cs in seen:
            continue
        seen.add(cs)
        out.append(a)
    return out
