"""Intent compiler: parse, classify, compile to action."""
import re


def parse_intent(text):
    text = text.strip().lower()
    verbs = ["create", "delete", "update", "list", "find", "send", "schedule"]
    verb = None
    for v in verbs:
        if text.startswith(v):
            verb = v
            break
    rest = text[len(verb):].strip() if verb else text
    return {"verb": verb or "unknown", "object": rest, "raw": text}


def classify(intent):
    if intent["verb"] in ("create", "update", "delete"):
        return "mutation"
    if intent["verb"] in ("list", "find"):
        return "query"
    return "action"


def compile_to_action(intent):
    return {"action": intent["verb"], "target": intent["object"], "params": {}}


def validate(intent):
    return intent["verb"] != "unknown" and bool(intent["object"])


def intent_confidence(intent, keywords):
    matches = sum(1 for k in keywords if k in intent["raw"])
    return round(min(1.0, matches / max(1, len(keywords))), 4)
