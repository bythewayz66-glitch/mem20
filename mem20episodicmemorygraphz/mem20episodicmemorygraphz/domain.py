"""Episodic memory graph: episodes, nodes, traversal, recall."""
import time, hashlib


def create_episode(title, events=None):
    return {"id": hashlib.sha256(title.encode()).hexdigest()[:8], "title": title, "events": events or [], "created_at": time.time()}


def add_event(ep, event):
    ep["events"].append({"ts": time.time(), **event})
    return ep


def link_episodes(episodes, a, b, relation="follows"):
    for e in episodes:
        if e["id"] == a:
            e.setdefault("links", []).append({"to": b, "relation": relation})
    return episodes


def recall(episodes, query):
    q = query.lower()
    results = []
    for e in episodes:
        if q in e.get("title", "").lower():
            results.append(e)
        for ev in e.get("events", []):
            if q in str(ev).lower():
                results.append(e)
                break
    return results


def episode_graph(episodes):
    nodes = [{"id": e["id"], "title": e["title"]} for e in episodes]
    edges = []
    for e in episodes:
        for link in e.get("links", []):
            edges.append({"from": e["id"], "to": link["to"], "relation": link["relation"]})
    return {"nodes": nodes, "edges": edges}


def forget(episodes, older_than):
    cutoff = time.time() - older_than
    return [e for e in episodes if e.get("created_at", 0) >= cutoff]
