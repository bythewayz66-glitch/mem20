"""Ambient device companion: context sensing, proactive suggestions, routines."""
import math, time


def sense_context(signals):
    """Infer context from sensor signals."""
    hour = signals.get("hour", 12)
    motion = signals.get("motion", 0)
    location = signals.get("location", "unknown")
    if motion > 0.5 and location != "home":
        return "commuting"
    if motion < 0.1 and location == "home":
        if 22 <= hour or hour <= 6:
            return "sleeping"
        return "relaxing"
    if motion > 0.3:
        return "active"
    return "idle"


def proactive_suggestion(context, history):
    """Suggest an action based on context and history."""
    suggestions = {
        "commuting": "play podcast",
        "sleeping": "enable do-not-disturb",
        "relaxing": "suggest music",
        "active": "track workout",
        "idle": "show notifications",
    }
    return suggestions.get(context, "none")


def routine_match(context, routines):
    """Find matching routine for context."""
    for r in routines:
        if r.get("trigger_context") == context:
            return r
    return None


def companion_mood(signals):
    """Derive companion mood from signals."""
    battery = signals.get("battery", 1.0)
    stress = signals.get("stress", 0.0)
    if battery < 0.2:
        return "concerned"
    if stress > 0.7:
        return "supportive"
    return "cheerful"


def ambient_score(signals):
    """Overall ambient engagement score."""
    return round(min(1.0, signals.get("motion", 0) * 0.4 + signals.get("interaction", 0) * 0.6), 4)
