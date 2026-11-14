"""Cross-runtime event lattice: events, ordering, causality."""
import time, uuid


def emit(event_type, payload, source="local"):
    return {"id": str(uuid.uuid4())[:8], "type": event_type, "payload": payload, "source": source, "ts": time.time(), "vector": {}}


def order_events(events):
    return sorted(events, key=lambda e: e.get("ts", 0))


def causal_link(parent, child):
    child["parent"] = parent.get("id")
    child["vector"] = {**parent.get("vector", {}), parent.get("id"): parent.get("ts")}
    return child


def lattice_merge(lattices):
    merged = []
    for L in lattices:
        merged.extend(L.get("events", []))
    return {"events": order_events(merged), "count": len(merged)}


def filter_by_type(events, etype):
    return [e for e in events if e.get("type") == etype]
