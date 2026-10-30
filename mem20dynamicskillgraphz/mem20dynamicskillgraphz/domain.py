"""Dynamic skill graph: nodes, edges, proficiency, learning paths."""
import math


def add_skill(graph, skill, prereqs=None):
    graph.setdefault("skills", {})[skill] = {"name": skill, "prereqs": prereqs or [], "proficiency": 0.0}
    return graph


def update_proficiency(graph, skill, delta):
    if skill in graph.get("skills", {}):
        graph["skills"][skill]["proficiency"] = min(1.0, max(0.0, graph["skills"][skill]["proficiency"] + delta))
    return graph


def learning_path(graph, target):
    # topological from prereqs
    path = []
    visited = set()
    def dfs(s):
        if s in visited:
            return
        for p in graph.get("skills", {}).get(s, {}).get("prereqs", []):
            dfs(p)
        visited.add(s)
        path.append(s)
    dfs(target)
    return path


def skill_gap(graph, required):
    gaps = []
    for r in required:
        prof = graph.get("skills", {}).get(r, {}).get("proficiency", 0.0)
        if prof < 1.0:
            gaps.append({"skill": r, "proficiency": prof, "gap": round(1.0 - prof, 3)})
    return gaps


def graph_stats(graph):
    skills = graph.get("skills", {})
    return {"count": len(skills), "avg_proficiency": round(sum(s["proficiency"] for s in skills.values()) / max(1, len(skills)), 4)}
