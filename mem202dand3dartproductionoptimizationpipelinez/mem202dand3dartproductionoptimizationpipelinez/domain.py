"""2D/3D art production optimization pipeline: asset budgeting, LOD, batching."""
import math


def lod_level(poly_count, target_fps=60, budget_ms=16.6):
    """Compute LOD level index from poly count and frame budget."""
    if poly_count <= 0:
        return 0
    # rough: each 10k polys ~ 1ms
    ms = poly_count / 10000.0
    if ms <= budget_ms * 0.25:
        return 0
    if ms <= budget_ms * 0.5:
        return 1
    if ms <= budget_ms * 0.75:
        return 2
    return 3


def texture_memory(width, height, channels=4, mipmaps=True):
    """Estimate texture memory in bytes."""
    base = width * height * channels
    if mipmaps:
        base = int(base * 1.333)
    return base


def batch_efficiency(asset_count, batch_size=64):
    """Compute batching efficiency and batch count."""
    if asset_count <= 0:
        return {"batches": 0, "efficiency": 0.0}
    batches = math.ceil(asset_count / batch_size)
    efficiency = asset_count / (batches * batch_size)
    return {"batches": batches, "efficiency": round(efficiency, 4)}


def optimize_pipeline(assets):
    """Optimize a list of assets: assign LOD, batch, estimate memory."""
    out = []
    total_mem = 0
    for a in assets:
        polys = int(a.get("polys", 0))
        w = int(a.get("tex_w", 512))
        h = int(a.get("tex_h", 512))
        lod = lod_level(polys)
        mem = texture_memory(w, h)
        total_mem += mem
        out.append({"id": a.get("id"), "lod": lod, "texture_bytes": mem, "polys": polys})
    batches = batch_efficiency(len(assets))
    return {"assets": out, "total_texture_bytes": total_mem, "batches": batches}


def frame_budget(fps=60):
    return round(1000.0 / fps, 3)
