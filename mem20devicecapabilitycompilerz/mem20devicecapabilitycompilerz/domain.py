"""Device capability compiler: capability detection, codegen, optimization."""
import platform


def detect_capabilities(device):
    caps = {
        "cpu_cores": device.get("cpu_cores", 1),
        "gpu": device.get("gpu", False),
        "memory_gb": device.get("memory_gb", 1),
        "storage_gb": device.get("storage_gb", 10),
        "network": device.get("network", "wifi"),
    }
    # derived
    caps["can_run_ml"] = caps["memory_gb"] >= 4 and caps["cpu_cores"] >= 2
    caps["can_render_3d"] = caps["gpu"] and caps["memory_gb"] >= 2
    caps["tier"] = "high" if caps["memory_gb"] >= 8 else "mid" if caps["memory_gb"] >= 4 else "low"
    return caps


def compile_for_device(code, caps):
    opts = []
    if caps.get("can_run_ml"):
        opts.append("ml_acceleration")
    if caps.get("can_render_3d"):
        opts.append("gpu_rendering")
    if caps.get("tier") == "low":
        opts.append("low_memory_mode")
    return {"code": code, "optimizations": opts, "target": caps.get("tier")}


def feature_flags(caps):
    return {
        "offline_mode": True,
        "heavy_animations": caps.get("tier") != "low",
        "ml_features": caps.get("can_run_ml", False),
        "3d_view": caps.get("can_render_3d", False),
    }


def compatibility(device, requirements):
    caps = detect_capabilities(device)
    missing = []
    for r in requirements:
        if r == "gpu" and not caps["gpu"]:
            missing.append(r)
        if r == "ml" and not caps["can_run_ml"]:
            missing.append(r)
        if r == "memory_4gb" and caps["memory_gb"] < 4:
            missing.append(r)
    return {"compatible": not missing, "missing": missing}
