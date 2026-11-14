"""Autonomous software foundry: spec to code, test, deploy, and estate report."""
from __future__ import annotations
import hashlib
from . import ecosystem
__all__=["spec_to_tasks","code_quality","deploy_decision","estimate_effort","build_artifact","foundry_report","probe","estate_context"]

def spec_to_tasks(spec):
    tasks=[{"id":f"task-{f}","feature":f,"status":"todo"} for f in spec.get("features",[])]
    tasks.append({"id":"tests","feature":"test suite","status":"todo"})
    tasks.append({"id":"deploy","feature":"deployment","status":"todo"})
    return tasks

def code_quality(metrics):
    score=0.0
    if metrics.get("tests_pass"): score+=0.4
    if metrics.get("coverage",0)>=0.8: score+=0.3
    if metrics.get("lint_clean"): score+=0.3
    return round(score,3)

def deploy_decision(quality, threshold=0.7): return quality>=threshold

def estimate_effort(spec):
    base=len(spec.get("features",[]))*2
    return {"days":base,"complexity":"high" if base>10 else "medium" if base>4 else "low"}

def build_artifact(spec, code):
    return {"name":spec.get("name"),"version":"0.1.0","checksum":hashlib.sha256(code.encode()).hexdigest()[:12],"size_lines":code.count(chr(10))}

def foundry_report(spec=None, code="print('hi')\n", metrics=None):
    spec=spec or {"name":"app","features":["auth","api"]}; metrics=metrics or {"tests_pass":True,"coverage":0.9,"lint_clean":True}
    tasks=spec_to_tasks(spec); qual=code_quality(metrics); deploy=deploy_decision(qual); effort=estimate_effort(spec); art=build_artifact(spec,code)
    peers={
        "capability_routing": ecosystem.capability_routing(spec.get("name","app"), ["lint","test","deploy"]),
        "artifact_recovery": ecosystem.artifact_recovery(art["name"]),
        "build_events": ecosystem.build_events("foundry.build", {"artifact":art["name"],"deploy":deploy}),
        "deploy_containment": ecosystem.deploy_containment("deploy"),
        "spec_quality": ecosystem.spec_quality(f"spec for {spec.get('name','app')}"),
        "effort_economics": ecosystem.effort_economics(effort["days"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"tasks":len(tasks),"quality":qual,"deploy":deploy,"effort":effort,"artifact":art,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=foundry_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
