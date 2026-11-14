"""Human-agent cowork canvas: shared workspace, turns, contributions."""
import time


def create_canvas(name, participants=None):
    return {"name": name, "participants": list(participants or []), "items": [], "turn": 0}


def add_item(canvas, author, content, kind="text"):
    item = {"id": len(canvas["items"]), "author": author, "content": content, "kind": kind, "ts": time.time()}
    canvas["items"].append(item)
    return item


def take_turn(canvas, participant):
    if participant not in canvas["participants"]:
        return {"ok": False, "error": "not a participant"}
    canvas["turn"] = (canvas["turn"] + 1) % len(canvas["participants"])
    return {"ok": True, "turn": canvas["turn"], "next": canvas["participants"][canvas["turn"]]}


def contributions(canvas):
    counts = {}
    for item in canvas["items"]:
        counts[item["author"]] = counts.get(item["author"], 0) + 1
    return counts


def canvas_summary(canvas):
    return {"name": canvas["name"], "items": len(canvas["items"]), "participants": len(canvas["participants"]), "turn": canvas["turn"]}
