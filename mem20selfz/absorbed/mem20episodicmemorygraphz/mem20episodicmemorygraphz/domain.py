"""Episodic Memory Graph (RM-021): experiences as linked episodes/entities/time.

Legacy-compatible API preserved: create_episode, add_event, link_episodes,
recall, episode_graph, forget.
"""
from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set


def _episode_id(title: Any, episode_id: Any = None, idempotency_key: Any = None) -> str:
    if episode_id is not None and str(episode_id).strip():
        return str(episode_id).strip()
    if idempotency_key is not None and str(idempotency_key).strip():
        return hashlib.sha256(f"episode-idem:{idempotency_key}".encode()).hexdigest()[:24]
    return uuid.uuid4().hex


# ---- legacy-compatible API ----

def create_episode(title, events=None, episode_id=None, idempotency_key=None):
    return {
        "id": _episode_id(title, episode_id=episode_id, idempotency_key=idempotency_key),
        "title": str(title),
        "events": list(events or []),
        "created_at": time.time(),
        "entities": [],
        "outcomes": [],
    }


def add_event(ep, event):
    ep.setdefault("events", []).append({"ts": time.time(), **dict(event)})
    # keep simple entity index for legacy recall/graph navigation
    for k in ("person", "place", "goal", "action", "outcome", "entity"):
        v = (event or {}).get(k)
        if v and v not in ep.setdefault("entities", []):
            ep["entities"].append(v)
    if (event or {}).get("outcome") and (event or {}).get("outcome") not in ep.setdefault("outcomes", []):
        ep["outcomes"].append((event or {}).get("outcome"))
    return ep


def link_episodes(episodes, a, b, relation="follows"):
    for e in episodes:
        if e.get("id") == a:
            e.setdefault("links", []).append({"to": b, "relation": relation, "ts": time.time()})
    return episodes


def recall(episodes, query):
    q = str(query).lower()
    results = []
    for e in episodes or []:
        if q in str(e.get("title", "")).lower():
            results.append(e); continue
        if any(q in str(x).lower() for x in e.get("entities", [])):
            results.append(e); continue
        for ev in e.get("events", []):
            if q in str(ev).lower():
                results.append(e); break
    return results


def episode_graph(episodes):
    nodes = [{"id": e.get("id"), "title": e.get("title"), "entities": e.get("entities", []), "created_at": e.get("created_at")}
             for e in episodes or []]
    edges = []
    for e in episodes or []:
        for link in e.get("links", []):
            edges.append({"from": e.get("id"), "to": link.get("to"), "relation": link.get("relation")})
    return {"nodes": nodes, "edges": edges}


def forget(episodes, older_than):
    cutoff = time.time() - float(older_than)
    return [e for e in episodes or [] if float(e.get("created_at", 0) or 0) >= cutoff]


# ---- advanced domain ----

@dataclass
class Episode:
    episode_id: str
    title: str
    events: List[Dict[str, Any]] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    outcomes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_legacy(self) -> Dict[str, Any]:
        return {"id": self.episode_id, "episode_id": self.episode_id, "title": self.title, "events": self.events,
                "entities": self.entities, "outcomes": self.outcomes, "tags": self.tags,
                "created_at": self.created_at, "metadata": self.metadata, "links": self.metadata.get("links", [])}


def add_episode_event(ep: Mapping[str, Any], event: Mapping[str, Any]) -> Dict[str, Any]:
    return add_event(dict(ep), dict(event))


def link_episode(episodes: Sequence[Mapping[str, Any]], src: str, dst: str, relation: str = "follows", weight: float = 1.0) -> List[Dict[str, Any]]:
    out = [dict(e) for e in episodes]
    for e in out:
        if e.get("id") == src or e.get("episode_id") == src:
            links = e.setdefault("links", [])
            links.append({"to": dst, "relation": relation, "weight": float(weight), "ts": time.time()})
    return out


def neighbors(episodes: Sequence[Mapping[str, Any]], episode_id: str) -> List[Dict[str, Any]]:
    out = []
    by_id = {e.get("id"): e for e in episodes or []}
    for e in episodes or []:
        if e.get("id") != episode_id:
            continue
        for l in e.get("links", []):
            out.append({"direction": "out", "to": l.get("to"), "relation": l.get("relation"), "node": by_id.get(l.get("to"))})
    for e in episodes or []:
        if any(l.get("to") == episode_id for l in e.get("links", [])):
            rel = next((l.get("relation") for l in e.get("links", []) if l.get("to") == episode_id), "linked")
            out.append({"direction": "in", "from": e.get("id"), "relation": rel, "node": e})
    return out


def timeline(episodes: Sequence[Mapping[str, Any]], limit: Optional[int] = None) -> List[Dict[str, Any]]:
    items = sorted((dict(e) for e in episodes or []), key=lambda e: float(e.get("created_at", 0) or 0))
    return items[:limit] if limit else items


def entity_index(episodes: Sequence[Mapping[str, Any]]) -> Dict[str, List[str]]:
    idx: Dict[str, List[str]] = {}
    for e in episodes or []:
        for ent in e.get("entities", []) or []:
            idx.setdefault(str(ent), []).append(e.get("id"))
    return idx


def context_diff(before: Sequence[Mapping[str, Any]], after: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    b = {e.get("id"): e for e in before or []}
    a = {e.get("id"): e for e in after or []}
    added = [k for k in a if k not in b]
    removed = [k for k in b if k not in a]
    changed = [k for k in a if k in b and (a[k].get("events") != b[k].get("events") or a[k].get("links") != b[k].get("links"))]
    return {"added": added, "removed": removed, "changed": changed, "ok": True}


def graph_query(episodes: Sequence[Mapping[str, Any]], entity: Optional[str] = None, relation: Optional[str] = None, since: Optional[float] = None, limit: int = 50) -> Dict[str, Any]:
    eps = [dict(e) for e in episodes or []]
    if since is not None:
        eps = [e for e in eps if float(e.get("created_at", 0) or 0) >= float(since)]
    if entity:
        eps = [e for e in eps if entity in (e.get("entities") or []) or entity.lower() in str(e.get("title", "")).lower() or any(entity.lower() in str(ev).lower() for ev in e.get("events", []))]
    g = episode_graph(eps)
    if relation:
        g["edges"] = [ed for ed in g["edges"] if ed.get("relation") == relation]
    return {"episodes": eps[:limit], "graph": g, "count": len(eps)}
