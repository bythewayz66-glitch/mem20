"""Dynamic skill graph: nodes, edges, proficiency, learning paths, with estate report."""
from __future__ import annotations
import math
from . import ecosystem
__all__=["add_skill","update_proficiency","learning_path","skill_gap","graph_stats","skill_report","probe","estate_context"]

def add_skill(graph, skill, prereqs=None):
    graph.setdefault("skills", {})[skill] = {"name": skill, "prereqs": prereqs or [], "proficiency": 0.0}
    return graph

def update_proficiency(graph, skill, delta):
    if skill in graph.get("skills", {}):
        graph["skills"][skill]["proficiency"] = min(1.0, max(0.0, graph["skills"][skill]["proficiency"] + delta))
    return graph

def learning_path(graph, target):
    path=[]; visited=set()
    def dfs(s):
        if s in visited: return
        for p in graph.get("skills", {}).get(s, {}).get("prereqs", []): dfs(p)
        visited.add(s); path.append(s)
    dfs(target); return path

def skill_gap(graph, required):
    gaps=[]
    for r in required:
        prof = graph.get("skills", {}).get(r, {}).get("proficiency", 0.0)
        if prof < 1.0: gaps.append({"skill": r, "proficiency": prof, "gap": round(1.0 - prof, 3)})
    return gaps

def graph_stats(graph):
    skills = graph.get("skills", {})
    return {"count": len(skills), "avg_proficiency": round(sum(s["proficiency"] for s in skills.values()) / max(1, len(skills)), 4)}

def skill_report(graph=None, target="advanced"):
    graph = graph or {}
    if not graph.get("skills"):
        add_skill(graph,"basics"); add_skill(graph,"intermediate",["basics"]); add_skill(graph,"advanced",["intermediate"])
        update_proficiency(graph,"basics",0.8); update_proficiency(graph,"intermediate",0.4)
    path=learning_path(graph,target); gaps=skill_gap(graph,[target,"intermediate"]); stats=graph_stats(graph)
    peers={
        "capability_match": ecosystem.capability_match("learner", list(graph.get("skills",{}).keys())[:3] or ["skill"]),
        "quest_progression": ecosystem.quest_progression(),
        "lifecycle_progression": ecosystem.lifecycle_progression(),
        "skill_events": ecosystem.skill_events("skill.report", {"target":target,"gaps":len(gaps),"avg":stats.get("avg_proficiency")}),
        "causal_routing": ecosystem.causal_routing({"gap":len(gaps)}, {"gap":0.5}),
        "context_compression": ecosystem.context_compression(" ".join(path) or "skills"),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"path":path,"gaps":gaps,"stats":stats,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=skill_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
