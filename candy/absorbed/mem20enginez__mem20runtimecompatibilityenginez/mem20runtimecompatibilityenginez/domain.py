"""Runtime compatibility engine: check version/env compatibility, with estate report."""
from __future__ import annotations
import sys, platform
from . import ecosystem
__all__=["check_python","check_deps","compatibility_report","suggest_fixes","runtime_report","probe","estate_context"]

def check_python(min_version=(3,11)):
    v=sys.version_info[:2]; return v >= min_version

def check_deps(deps, installed):
    missing=[d for d in deps if d not in installed]; return {"ok": not missing, "missing": missing}

def compatibility_report(env, requirements):
    report={}
    report["python_ok"]=check_python(requirements.get("python", (3, 11)))
    report["deps"]=check_deps(requirements.get("deps", []), env.get("installed", []))
    report["platform"]=platform.system()
    report["compatible"]=report["python_ok"] and report["deps"]["ok"]
    return report

def suggest_fixes(report):
    fixes=[]
    if not report.get("python_ok"): fixes.append("upgrade python")
    for m in report.get("deps", {}).get("missing", []): fixes.append(f"install {m}")
    return fixes

def runtime_report():
    req={"python":(3,11),"deps":[]}; env={"installed":[]}; rep=compatibility_report(env,req); fixes=suggest_fixes(rep)
    peers={
        "config_compat": ecosystem.config_compat({"python":".".join(map(str,req["python"]))}),
        "capability_routing": ecosystem.capability_routing("runtime", ["check","fix","report"]),
        "compat_events": ecosystem.compat_events("compat.report", {"compatible":rep.get("compatible"),"fixes":len(fixes)}),
        "check_containment": ecosystem.check_containment("compatibility"),
        "healing_fixes": ecosystem.healing_fixes(fixes or ["noop"]),
        "device_runtime": ecosystem.device_runtime({"cpu":True,"platform":rep.get("platform")}),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and rep.get("compatible",False),"compatible":rep.get("compatible"),"fixes":fixes,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=runtime_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
