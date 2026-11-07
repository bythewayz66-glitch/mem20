"""Rigging, animation and motion pipeline, with estate report."""
from __future__ import annotations
import math
from . import ecosystem
__all__=["create_rig","set_pose","animate","motion_blend","rig_health","rig_report","probe","estate_context"]

def create_rig(bones):
    return {"bones": list(bones), "constraints": [], "pose": {b: (0,0,0) for b in bones}}

def set_pose(rig, bone, rotation):
    if bone in rig["pose"]: rig["pose"][bone] = rotation
    return rig

def animate(rig, frames):
    poses=[]
    for f in frames:
        p=dict(rig["pose"])
        for bone, rot in f.get("pose", {}).items(): p[bone]=rot
        poses.append(p)
    return poses

def motion_blend(a, b, alpha):
    out={}
    for k in set(a)|set(b):
        va=a.get(k,(0,0,0)); vb=b.get(k,(0,0,0))
        out[k]=tuple(alpha*va[i] + (1-alpha)*vb[i] for i in range(3))
    return out

def rig_health(rig):
    return {"bones": len(rig["bones"]), "posed": len(rig["pose"])}

def rig_report():
    rig=create_rig(["spine","arm"]); set_pose(rig,"arm",(10,0,0)); poses=animate(rig,[{"pose":{"arm":(20,0,0)}}]); h=rig_health(rig)
    peers={
        "device_compile": ecosystem.device_compile({"gpu":True,"cpu":True},"anim_shader"),
        "data_locality": ecosystem.data_locality({"bones":len(rig["bones"])},"local"),
        "animation_events": ecosystem.animation_events("rig.report", {"bones":h["bones"],"frames":len(poses)}),
        "pipeline_containment": ecosystem.pipeline_containment("animate"),
        "capability_routing": ecosystem.capability_routing("rig", ["rig","animate","blend"]),
        "config_validation": ecosystem.config_validation({"name":"rig","bones":h["bones"]}),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"bones":h["bones"],"frames":len(poses),"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=rig_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
