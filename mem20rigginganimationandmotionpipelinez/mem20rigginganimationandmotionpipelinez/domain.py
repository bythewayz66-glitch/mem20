"""Rigging, animation and motion pipeline."""
import math


def create_rig(bones):
    return {"bones": list(bones), "constraints": [], "pose": {b: (0,0,0) for b in bones}}


def set_pose(rig, bone, rotation):
    if bone in rig["pose"]:
        rig["pose"][bone] = rotation
    return rig


def animate(rig, frames):
    poses = []
    for f in frames:
        p = dict(rig["pose"])
        for bone, rot in f.get("pose", {}).items():
            p[bone] = rot
        poses.append(p)
    return poses


def motion_blend(a, b, alpha):
    out = {}
    for k in set(a) | set(b):
        va = a.get(k, (0,0,0)); vb = b.get(k, (0,0,0))
        out[k] = tuple(alpha*va[i] + (1-alpha)*vb[i] for i in range(3))
    return out


def rig_health(rig):
    return {"bones": len(rig["bones"]), "posed": len(rig["pose"])}
