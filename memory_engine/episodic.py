"""Episodic memory -- first-class memory_engine capability.

Episodes are sequences of grounded experiences, stored on the ledger via
remember/recall (not an in-memory list). Formerly mem20episodicmemorygraphz.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _topic(episode_id: str) -> str:
    return f"episode:{episode_id}"


def _link_topic(a: str, b: str) -> str:
    return f"episode_link:{a}:{b}"


@dataclass
class Episode:
    id: str
    title: str
    events: list[dict[str, Any]] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    outcomes: list[str] = field(default_factory=list)
    links: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = 0.0
    fact_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "events": list(self.events),
            "entities": list(self.entities),
            "outcomes": list(self.outcomes),
            "links": list(self.links),
            "created_at": self.created_at,
            "fact_id": self.fact_id,
        }


def create_episode(
    title: str,
    events: list | None = None,
    *,
    episode_id: str | None = None,
    persist: bool = True,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Create an episode and optionally persist it as a grounded fact."""
    eid = (episode_id or uuid.uuid4().hex)[:32]
    ep = Episode(
        id=eid,
        title=str(title),
        events=list(events or []),
        created_at=time.time(),
    )
    for ev in ep.events:
        _index_event(ep, ev)
    if persist:
        _persist(ep, tags=tags)
    return ep.to_dict()


def add_event(episode: dict[str, Any], event: dict[str, Any], *, persist: bool = True) -> dict[str, Any]:
    """Append an event to an episode dict; re-persist if requested."""
    ep = _from_dict(episode)
    payload = {"ts": time.time(), **dict(event or {})}
    ep.events.append(payload)
    _index_event(ep, payload)
    if persist:
        _persist(ep)
    return ep.to_dict()


def link_episodes(
    a: str,
    b: str,
    relation: str = "follows",
    *,
    persist: bool = True,
) -> dict[str, Any]:
    """Record a directed link between two episode ids on the ledger."""
    link = {"from": a, "to": b, "relation": relation, "ts": time.time()}
    if persist:
        try:
            from memory_engine import remember
            remember(
                topic=_link_topic(a, b),
                content=json.dumps(link),
                tags=["episode_link", relation, a, b],
                epistemic_status="observed",
            )
        except Exception as exc:
            link["persist_error"] = f"{type(exc).__name__}: {exc}"
    return link


def recall_episodes(query: str, *, k: int = 20) -> list[dict[str, Any]]:
    """Recall episodes whose title/entities/events match query (grounded ledger)."""
    episodes = list_episodes(k=200)
    q = str(query).lower()
    out = []
    for e in episodes:
        if q in str(e.get("title", "")).lower():
            out.append(e)
            continue
        if any(q in str(x).lower() for x in e.get("entities") or []):
            out.append(e)
            continue
        if any(q in str(ev).lower() for ev in e.get("events") or []):
            out.append(e)
    return out[:k]


def episode_graph(episodes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Nodes + edges for episodes (from list or ledger)."""
    if episodes is None:
        episodes = list_episodes(k=200)
    nodes = [
        {
            "id": e.get("id"),
            "title": e.get("title"),
            "entities": e.get("entities") or [],
            "created_at": e.get("created_at"),
        }
        for e in episodes
    ]
    edges = []
    for e in episodes:
        for link in e.get("links") or []:
            edges.append({
                "from": e.get("id"),
                "to": link.get("to"),
                "relation": link.get("relation", "follows"),
            })
    try:
        from memory_engine import recall
        for r in recall(topic="episode_link:", k=100, include_simulated=False) or []:
            try:
                link = json.loads(r.get("content") or "{}")
                edges.append({
                    "from": link.get("from"),
                    "to": link.get("to"),
                    "relation": link.get("relation", "follows"),
                })
            except Exception:
                continue
    except Exception:
        pass
    return {"nodes": nodes, "edges": edges}


def forget_episode(episode_id: str) -> dict[str, Any]:
    """Supersede the grounded episode fact with a tombstone."""
    try:
        from memory_engine import recall, supersede
        rows = recall(topic=_topic(episode_id), k=5, include_simulated=False) or []
        if not rows:
            return {"ok": False, "error": "not_found", "id": episode_id}
        rid = rows[0].get("id")
        supersede(rid, f"[forgotten episode {episode_id}]", epistemic_status="observed")
        return {"ok": True, "id": episode_id, "superseded": rid}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "id": episode_id}


def list_episodes(*, k: int = 50) -> list[dict[str, Any]]:
    """Load recent episode facts from the grounded ledger."""
    try:
        from memory_engine import recall
        rows = recall(topic="episode:", k=k, include_simulated=False) or []
    except Exception:
        return []
    out = []
    for r in rows:
        try:
            data = json.loads(r.get("content") or "{}")
            if isinstance(data, dict) and data.get("id"):
                data["fact_id"] = r.get("id")
                out.append(data)
        except Exception:
            continue
    return out


def episodic_health() -> dict[str, Any]:
    eps = list_episodes(k=5)
    return {"ok": True, "sample_count": len(eps), "backend": "memory_engine.ledger"}


def _index_event(ep: Episode, event: dict) -> None:
    for k in ("person", "place", "goal", "action", "outcome", "entity"):
        v = (event or {}).get(k)
        if v and str(v) not in ep.entities:
            ep.entities.append(str(v))
    if (event or {}).get("outcome"):
        o = str(event["outcome"])
        if o not in ep.outcomes:
            ep.outcomes.append(o)


def _from_dict(d: dict) -> Episode:
    return Episode(
        id=str(d.get("id") or uuid.uuid4().hex),
        title=str(d.get("title") or ""),
        events=list(d.get("events") or []),
        entities=list(d.get("entities") or []),
        outcomes=list(d.get("outcomes") or []),
        links=list(d.get("links") or []),
        created_at=float(d.get("created_at") or time.time()),
        fact_id=d.get("fact_id"),
    )


def _persist(ep: Episode, tags: list[str] | None = None) -> None:
    from memory_engine import remember, supersede, recall
    payload = json.dumps(ep.to_dict())
    tag_list = list(tags or []) + ["episode", ep.id]
    try:
        prev = recall(topic=_topic(ep.id), k=1, include_simulated=False) or []
        if prev and prev[0].get("id"):
            row = supersede(prev[0]["id"], payload, epistemic_status="observed")
            ep.fact_id = (row or {}).get("id") if isinstance(row, dict) else prev[0].get("id")
            return
    except Exception:
        pass
    row = remember(
        topic=_topic(ep.id),
        content=payload,
        tags=tag_list,
        epistemic_status="observed",
    )
    if isinstance(row, dict):
        ep.fact_id = row.get("id")
