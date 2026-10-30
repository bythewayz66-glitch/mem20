"""Event stream superhighway: publish, subscribe, routing, throughput."""
import time, uuid, collections


def create_stream(name):
    return {"name": name, "events": [], "subscribers": {}, "seq": 0}


def publish(stream, event_type, payload, key=None):
    stream["seq"] += 1
    ev = {"seq": stream["seq"], "type": event_type, "payload": payload, "key": key, "ts": time.time()}
    stream["events"].append(ev)
    return ev


def subscribe(stream, subscriber_id, filter_type=None):
    stream["subscribers"][subscriber_id] = {"filter": filter_type, "offset": 0}
    return stream


def consume(stream, subscriber_id, batch=10):
    sub = stream["subscribers"].get(subscriber_id)
    if not sub:
        return []
    offset = sub["offset"]
    events = stream["events"][offset:offset + batch]
    if sub["filter"]:
        events = [e for e in events if e["type"] == sub["filter"]]
    sub["offset"] += len(stream["events"][offset:offset + batch])
    return events


def throughput(stream, window_s=60):
    now = time.time()
    recent = [e for e in stream["events"] if now - e["ts"] <= window_s]
    return round(len(recent) / window_s * 60, 2)


def lag(stream, subscriber_id):
    sub = stream["subscribers"].get(subscriber_id)
    if not sub:
        return 0
    return len(stream["events"]) - sub["offset"]
