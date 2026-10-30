"""Real-time event autopilot: event stream, rules, actions."""
import time


def ingest_event(stream, event):
    stream.setdefault("events", []).append({**event, "ts": time.time()})
    return stream


def evaluate_rules(event, rules):
    actions = []
    for r in rules:
        if r.get("condition", lambda e: False)(event):
            actions.append(r.get("action"))
    return actions


def autopilot(stream, rules):
    results = []
    for e in stream.get("events", []):
        acts = evaluate_rules(e, rules)
        results.append({"event": e, "actions": acts})
    return results


def throttle(stream, max_per_sec=10):
    # simple: keep last max_per_sec*1 events
    events = stream.get("events", [])
    if len(events) > max_per_sec:
        stream["events"] = events[-max_per_sec:]
    return stream


def autopilot_health(stream):
    return {"events": len(stream.get("events", []))}
