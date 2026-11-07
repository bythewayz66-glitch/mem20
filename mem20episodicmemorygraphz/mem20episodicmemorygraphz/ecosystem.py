"""Six unique peers for episodic memory graph (#306), different from #300-#305."""
from __future__ import annotations
from typing import Any, Dict, Mapping, Sequence

def _safe(name, fn):
    try: return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e: return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

# 1) mem20dynamicskillgraphz - skill/proficiency graph over episode outcomes/actions
def skill_graph(episodes: Sequence[Mapping[str, Any]] = None) -> Dict[str, Any]:
    def run():
        from mem20dynamicskillgraphz.domain import add_skill, update_proficiency, learning_path, skill_gap, graph_stats
        g = {"skills": {}, "edges": []}
        for ep in (episodes or [{"title": "debug", "events": [{"action": "trace"}], "outcomes": ["fixed"]}]):
            for ev in (ep.get("events") or []):
                act = str(ev.get("action") or ev.get("type") or "action")
                add_skill(g, act, prereqs=[])
                update_proficiency(g, act, 0.1)
            for out in (ep.get("outcomes") or []):
                add_skill(g, str(out), prereqs=[])
        target = next(iter(g.get("skills") or {"action": {}}.keys()))
        path = learning_path(g, target)
        gap = skill_gap(g, [target])
        stats = graph_stats(g)
        return {"target": target, "learning_path": path, "skill_gap": gap, "stats": stats}
    return _safe("mem20dynamicskillgraphz", run)

# 2) mem20reversibleexecutiongraphz - reversible episode/replay graph
def reversible_replay(events: Sequence[Mapping[str, Any]] = None) -> Dict[str, Any]:
    def run():
        from mem20reversibleexecutiongraphz.domain import create_graph, add_node, undo, redo, graph_health
        g = create_graph()
        for ev in (events or [{"id": "e1", "op": "create"}, {"id": "e2", "op": "link"}]):
            add_node(g, dict(ev))
        u = undo(g)
        r = redo(g)
        health = graph_health(g)
        return {"undo": u, "redo": r, "health": health}
    return _safe("mem20reversibleexecutiongraphz", run)

# 3) mem20mixedinitiativefocusenginez - focus/attention for recall lens
def recall_focus(context: Mapping[str, Any] = None, options: Sequence[Mapping[str, Any]] = None) -> Dict[str, Any]:
    def run():
        from mem20mixedinitiativefocusenginez.domain import focus_score, suggest, take_over, blend, focus_health
        ctx = dict(context or {"attention": 0.7, "load": 0.3, "goal": "recall"})
        opts = [dict(o) for o in (options or [{"id": "recent", "relevance": 0.8}, {"id": "related", "relevance": 0.6}])]
        score = focus_score(ctx)
        sugg = suggest(ctx, opts)
        take = take_over(score if isinstance(score, (int, float)) else 0.5, 0.6)
        blended = blend({"intent": "user-recall"}, {"intent": "agent-suggest"}, 0.5)
        health = focus_health(ctx)
        return {"focus_score": score, "suggestions": sugg, "take_over": take, "blend": blended, "health": health}
    return _safe("mem20mixedinitiativefocusenginez", run)

# 4) mem20spatialcommanduniversez - spatial/place indexing for episodes
def spatial_places(entities: Sequence[Mapping[str, Any]] = None) -> Dict[str, Any]:
    def run():
        from mem20spatialcommanduniversez.domain import create_region, add_entity, distance, in_region, spatial_health
        # bounds as [(min,max), (min,max)] per API contract
        region = create_region("episode-space", [(0, 100), (0, 100)])
        ents = [dict(e) for e in (entities or [{"id": "place:a", "kind": "place"}, {"id": "place:b", "kind": "place"}])]
        for i, e in enumerate(ents):
            add_entity(region, e, (10 + i * 10, 10 + i * 5))
        d = distance((10, 10), (20, 15))
        inside = in_region(region, (15, 12))
        health = spatial_health([region])
        return {"region": str(region.get("name") if isinstance(region, dict) else "episode-space"), "distance_sample": d, "in_region": inside, "health": health}
    return _safe("mem20spatialcommanduniversez", run)

# 5) mem20crossproductloyaltygraphz - relationship centrality/recommendations
def relationship_graph(episodes: Sequence[Mapping[str, Any]] = None) -> Dict[str, Any]:
    def run():
        from mem20crossproductloyaltygraphz.domain import add_edge, degree, centrality, recommend_products, loyalty_score
        g = {}
        eps = list(episodes or [{"id": "a", "entities": ["alice", "goal:ship"]}, {"id": "b", "entities": ["alice", "place:lab"]}])
        for ep in eps:
            ents = [str(x) for x in (ep.get("entities") or [])] or [str(ep.get("id"))]
            for i in range(len(ents)-1):
                add_edge(g, ents[i], ents[i+1], 1.0)
            if ents:
                add_edge(g, str(ep.get("id")), ents[0], 1.0)
        node = next(iter(g.keys()), "alice")
        deg = degree(g, node)
        cent = centrality(g)
        rec = recommend_products(g, [node], 3)
        loy = loyalty_score([node], g)
        return {"nodes": len(g), "degree_sample": deg, "centrality_keys": list(cent.keys())[:5] if isinstance(cent, dict) else None, "recommendations": rec, "loyalty": loy}
    return _safe("mem20crossproductloyaltygraphz", run)

# 6) mem20deterministicconfigurationgraphz - deterministic relationship/config resolution
def deterministic_links(episodes: Sequence[Mapping[str, Any]] = None) -> Dict[str, Any]:
    def run():
        from mem20deterministicconfigurationgraphz.domain import add_node, add_edge, resolve, validate, diff_configs
        g = {"nodes": {}, "edges": []}
        for ep in (episodes or [{"id": "a"}, {"id": "b", "links": [{"to": "a"}]}]):
            add_node(g, str(ep.get("id")), {"title": ep.get("title")})
            for l in (ep.get("links") or []):
                add_edge(g, str(ep.get("id")), str(l.get("to")))
        valid = validate(g)
        resolved = None
        node_id = next(iter((g.get("nodes") or {"a": {}}).keys()))
        try: resolved = resolve(g, node_id)
        except Exception as e: resolved = {"error": str(e)}
        diff = diff_configs({"nodes": 1}, {"nodes": 2})
        return {"valid": valid, "resolved_sample": resolved, "diff": diff}
    return _safe("mem20deterministicconfigurationgraphz", run)

def probe() -> Dict[str, Any]:
    checks = {
        "dynamic_skill_graph": skill_graph(),
        "reversible_execution": reversible_replay(),
        "focus_recall": recall_focus(),
        "spatial_places": spatial_places(),
        "relationship_graph": relationship_graph(),
        "deterministic_config": deterministic_links(),
    }
    reachable = [k for k,v in checks.items() if v.get("ok")]
    return {"ok": len(reachable)==6, "count": len(reachable), "reachable": reachable, "checks": checks}
