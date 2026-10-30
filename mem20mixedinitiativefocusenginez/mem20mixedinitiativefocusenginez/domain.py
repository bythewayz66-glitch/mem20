"""Mixed-initiative focus engine: attention, suggestions, takeover."""
import math


def focus_score(context):
    # higher when fewer distractions
    distractions = context.get("distractions", 0)
    priority = context.get("priority", 1)
    return round(priority / (1 + distractions), 4)


def suggest(context, options):
    scored = []
    for o in options:
        s = focus_score({**context, "priority": o.get("priority", 1)})
        scored.append((s, o))
    scored.sort(reverse=True)
    return [o for _, o in scored]


def take_over(initiative_level, threshold=0.5):
    return initiative_level >= threshold


def blend(user_intent, agent_intent, alpha=0.5):
    # alpha: weight of user intent
    return {"blended_priority": alpha*user_intent.get("priority",0)+(1-alpha)*agent_intent.get("priority",0)}


def focus_health(context):
    return {"score": focus_score(context), "healthy": focus_score(context) > 0.3}
