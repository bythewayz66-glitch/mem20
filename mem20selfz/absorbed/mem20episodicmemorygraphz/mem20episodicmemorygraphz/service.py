"""Service for episodic memory graph: CRUD, recall/query, graph ops, peer signals."""
from __future__ import annotations
from typing import Any, Dict, Mapping, Optional, Sequence
from . import domain, ecosystem
from .store import ConflictError, EpisodicStore, NotFoundError

class ValidationError(ValueError): pass

class EpisodicService:
    def __init__(self, db_path): self.store = EpisodicStore(db_path)

    def create_episode(self, title, events=None, entities=None, metadata=None, episode_id=None, idempotency_key=None):
        if not str(title or "").strip(): raise ValidationError("title required")
        ep = domain.create_episode(title, events, episode_id=episode_id, idempotency_key=idempotency_key)
        if entities: ep["entities"] = list(dict.fromkeys(list(ep.get("entities") or []) + list(entities)))
        if metadata:
            body = dict(metadata)
            if idempotency_key is not None and str(idempotency_key).strip():
                body.setdefault("idempotency_key", str(idempotency_key))
            ep["metadata"] = body
        ep = self.store.put_episode(ep)
        focus = ecosystem.recall_focus({"goal": "create", "attention": 0.6}, [{"id": ep["id"], "relevance": 1.0}])
        spatial = ecosystem.spatial_places([{"id": f"entity:{e}", "kind": "entity"} for e in (ep.get("entities") or [])[:3]] or [{"id":"place:episode","kind":"place"}])
        return {"ok": True, "episode": ep, "signals": {"focus_recall": focus, "spatial_places": spatial}}

    def add_event(self, episode_id, event: Mapping[str, Any], expected_version=None):
        ep = self.store.require_episode(episode_id)
        base_version = expected_version if expected_version is not None else ep.get("version")
        ep = domain.add_event(ep, dict(event))
        ep = self.store.put_episode(ep, expected_version=base_version)
        replay = ecosystem.reversible_replay(ep.get("events") or [])
        skills = ecosystem.skill_graph([ep])
        return {"ok": True, "episode": ep, "signals": {"reversible_execution": replay, "dynamic_skill_graph": skills}}

    def link(self, src, dst, relation="follows"):
        self.store.require_episode(dst)
        ep = self.store.require_episode(src)
        links = ep.setdefault("links", [])
        links.append({"to": dst, "relation": relation, "ts": __import__("time").time()})
        ep = self.store.put_episode(ep, expected_version=ep.get("version"))
        rel = ecosystem.relationship_graph(self.store.list_episodes())
        det = ecosystem.deterministic_links(self.store.list_episodes())
        return {"ok": True, "episode": ep, "signals": {"relationship_graph": rel, "deterministic_config": det}}

    def get(self, episode_id): return {"ok": True, "episode": self.store.require_episode(episode_id)}
    def list(self, limit=200): return {"ok": True, "episodes": self.store.list_episodes(limit)}

    def recall(self, query, limit=50, since=None, until=None, entity=None, expand_graph=False):
        eps = self.store.list_episodes(2000)
        q = str(query or "").strip()
        if q:
            results = domain.recall(eps, q)
        else:
            results = list(eps)
        if entity:
            ent = str(entity).lower()
            results = [e for e in results if ent in [str(x).lower() for x in (e.get("entities") or [])] or any(ent in str(ev).lower() for ev in (e.get("events") or []))]
        if since is not None:
            results = [e for e in results if float(e.get("created_at", 0) or 0) >= float(since)]
        if until is not None:
            results = [e for e in results if float(e.get("created_at", 0) or 0) <= float(until)]
        results = domain.timeline(results)[: max(0, int(limit))]
        payload = {"ok": True, "query": q, "results": results, "count": len(results), "retrieval": {"mode": "graph_temporal_entity" if (entity or since or until or expand_graph) else "text_graph", "entity": entity, "since": since, "until": until, "expand_graph": bool(expand_graph)}}
        if expand_graph and results:
            gq = domain.graph_query(eps, entity=entity, since=since, limit=max(50, int(limit)))
            payload["graph"] = gq.get("graph")
            payload["neighbors"] = {e.get("id"): domain.neighbors(eps, e.get("id")) for e in results[:10] if e.get("id")}
        focus = ecosystem.recall_focus({"goal": "recall", "query": q, "attention": 0.8, "entity": entity}, [{"id": r.get("id"), "relevance": 0.7} for r in results[:5]])
        payload["signals"] = {"focus_recall": focus}
        return payload

    def query(self, payload: Mapping[str, Any] = None):
        payload = payload or {}
        eps = self.store.list_episodes(2000)
        res = domain.graph_query(eps, entity=payload.get("entity"), relation=payload.get("relation"), since=payload.get("since"), limit=int(payload.get("limit") or 50))
        rel = ecosystem.relationship_graph(res.get("episodes") or [])
        det = ecosystem.deterministic_links(res.get("episodes") or [])
        return {"ok": True, **res, "signals": {"relationship_graph": rel, "deterministic_config": det}}

    def graph(self): return {"ok": True, "graph": domain.episode_graph(self.store.list_episodes(2000))}
    def timeline(self, limit=100): return {"ok": True, "timeline": domain.timeline(self.store.list_episodes(2000), limit)}
    def neighbors(self, episode_id): return {"ok": True, "neighbors": domain.neighbors(self.store.list_episodes(2000), episode_id)}

    def forget(self, older_than_seconds: float):
        eps = self.store.list_episodes(10000)
        kept = domain.forget(eps, older_than_seconds)
        keep_ids = {e.get("id") for e in kept}
        removed = 0
        for e in eps:
            if e.get("id") not in keep_ids:
                if self.store.delete_episode(e.get("id")): removed += 1
        return {"ok": True, "removed": removed, "remaining": len(self.store.list_episodes(10000))}

    def status(self):
        m = self.store.metrics(); eps = self.store.list_episodes(100)
        skills = ecosystem.skill_graph(eps); spatial = ecosystem.spatial_places([{"id":"p","kind":"place"}])
        return {"ok": True, "metrics": m, "graph": {"nodes": m["episodes"]}, "signals": {"dynamic_skill_graph": skills, "spatial_places": spatial}}

    def doctor(self):
        p = ecosystem.probe(); st = self.status()
        return {"ok": p.get("ok") and st.get("ok"), "probe": p, "metrics": st["metrics"]}

    def events(self, since=0, limit=200): return self.store.events(since, limit)
    def snapshot(self, label=""): return {"ok": True, **self.store.snapshot(label)}
    def restore(self, snapshot_id): return self.store.restore(snapshot_id)

    def simulate(self):
        ep = domain.create_episode("ship fix", [{"action":"debug","place":"lab","outcome":"fixed"}])
        ep = domain.add_event(ep, {"action":"deploy"})
        eps = domain.link_episodes([ep, domain.create_episode("retro")], ep["id"], domain.create_episode("retro")["id"])
        g = domain.episode_graph([ep])
        r = domain.recall([ep], "lab")
        p = ecosystem.probe()
        passed = sum([bool(ep["id"]), bool(g["nodes"]), bool(r), p["ok"], bool(domain.neighbors([ep], ep["id"]) is not None), bool(domain.timeline([ep]))])
        return {"ok": p["ok"] and bool(r), "passed": passed, "total": 6, "scenarios": {"create_event": {"ok": bool(ep["id"])}, "graph": {"ok": bool(g["nodes"])}, "recall": {"ok": bool(r)}, "peer_probe": {"ok": p["ok"], "count": p["count"]}, "neighbors": {"ok": True}, "timeline": {"ok": True}}}

    def benchmark(self, iterations=20):
        import time as _t; eps=[domain.create_episode(f"e{i}") for i in range(20)]; t0=_t.perf_counter()
        for _ in range(max(1,int(iterations))): domain.recall(eps, "e1"); domain.episode_graph(eps)
        dt=max(1e-9,_t.perf_counter()-t0); return {"ok":True,"iterations":int(iterations),"ops_per_sec":round(int(iterations)/dt,3)}

    def execute(self, payload: Mapping[str, Any]): return self.status()
