"""Asset remix studio: combine, transform, and export assets."""
import hashlib, math


def remix(assets, operations):
    """Apply a list of operations to combine assets."""
    result = {"sources": [a.get("id") for a in assets], "operations": operations, "output": None}
    # simple: merge metadata
    merged = {}
    for a in assets:
        merged.update(a.get("metadata", {}))
    for op in operations:
        if op == "grayscale":
            merged["filter"] = "grayscale"
        elif op == "resize":
            merged["resized"] = True
        elif op == "crop":
            merged["cropped"] = True
    result["output"] = merged
    result["checksum"] = hashlib.sha256(str(merged).encode()).hexdigest()[:12]
    return result


def transform_asset(asset, transform):
    """Apply a single transform to an asset."""
    out = dict(asset)
    if transform == "scale":
        out["scale"] = asset.get("scale", 1.0) * 2
    elif transform == "rotate":
        out["rotation"] = (asset.get("rotation", 0) + 90) % 360
    elif transform == "flip":
        out["flipped"] = True
    return out


def export_formats(asset, formats):
    """List export targets."""
    return [{"format": f, "asset": asset.get("id"), "estimated_size": asset.get("size", 0) * (1.2 if f == "png" else 1.0)} for f in formats]


def blend_assets(a, b, ratio=0.5):
    """Blend two assets' metadata by ratio."""
    merged = {}
    for k in set(a.get("metadata", {})) | set(b.get("metadata", {})):
        va = a.get("metadata", {}).get(k, 0)
        vb = b.get("metadata", {}).get(k, 0)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            merged[k] = round(va * ratio + vb * (1 - ratio), 4)
        else:
            merged[k] = va if ratio >= 0.5 else vb
    return {"metadata": merged, "ratio": ratio}


def remix_variants(asset, count=4):
    """Generate remix variants."""
    variants = []
    for i in range(count):
        variants.append({"id": f"{asset.get('id')}_v{i}", "transform": ["scale", "rotate", "flip"][i % 3]})
    return variants
