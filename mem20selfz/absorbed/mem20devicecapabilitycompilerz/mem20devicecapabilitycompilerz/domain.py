"""Device capability compiler: capability detection, codegen, optimization, with estate report."""
from __future__ import annotations
import platform
from . import ecosystem
__all__=["detect_capabilities","compile_for_device","feature_flags","compatibility","compile_report","probe","estate_context"]

def detect_capabilities(device):
    caps = {
        "cpu_cores": device.get("cpu_cores", 1),
        "gpu": device.get("gpu", False),
        "memory_gb": device.get("memory_gb", 1),
        "storage_gb": device.get("storage_gb", 10),
        "network": device.get("network", "wifi"),
    }
    caps["can_run_ml"] = caps["memory_gb"] >= 4 and caps["cpu_cores"] >= 2
    caps["can_render_3d"] = caps["gpu"] and caps["memory_gb"] >= 2
    caps["tier"] = "high" if caps["memory_gb"] >= 8 else "mid" if caps["memory_gb"] >= 4 else "low"
    return caps

def compile_for_device(code, caps):
    opts = []
    if caps.get("can_run_ml"): opts.append("ml_acceleration")
    if caps.get("can_render_3d"): opts.append("gpu_rendering")
    if caps.get("tier") == "low": opts.append("low_memory_mode")
    return {"code": code, "optimizations": opts, "target": caps.get("tier")}

def feature_flags(caps):
    return {"offline_mode": True, "heavy_animations": caps.get("tier") != "low", "ml_features": caps.get("can_run_ml", False), "3d_view": caps.get("can_render_3d", False)}

def compatibility(device, requirements):
    caps = detect_capabilities(device)
    missing = []
    for r in requirements:
        if r == "gpu" and not caps["gpu"]: missing.append(r)
        if r == "ml" and not caps["can_run_ml"]: missing.append(r)
        if r == "memory_4gb" and caps["memory_gb"] < 4: missing.append(r)
    return {"compatible": not missing, "missing": missing}

def compile_report(device=None, code="app"):
    device = device or {"id":"d1","cpu_cores":4,"gpu":False,"memory_gb":8,"storage_gb":64,"network":"wifi"}
    caps=detect_capabilities(device); compiled=compile_for_device(code,caps); flags=feature_flags(caps); compat=compatibility(device,["memory_4gb"])
    peers={
        "platform_context": ecosystem.platform_context(),
        "artifact_placement": ecosystem.artifact_placement(0.5),
        "device_fleet": ecosystem.device_fleet(device.get("id","d1")),
        "capability_match": ecosystem.capability_match(caps.get("tier","low"), compiled.get("optimizations") or ["base"]),
        "compile_events": ecosystem.compile_events("compile.report", {"tier":caps.get("tier"),"opts":len(compiled.get("optimizations",[]))}),
        "device_health": ecosystem.device_health([device.get("id","d1")]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"tier":caps.get("tier"),"compatible":compat.get("compatible"),"optimizations":compiled.get("optimizations"),"feature_flags":flags,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=compile_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
