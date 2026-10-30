"""Visual agent blackboard: shared visual state for agents."""
import time


def create_blackboard(name):
    return {"name": name, "items": [], "agents": set()}


def post(bb, agent, item):
    bb["items"].append({"agent": agent, "item": item, "ts": time.time()})
    bb["agents"].add(agent)
    return bb


def read(bb, agent=None):
    if agent:
        return [i for i in bb["items"] if i["agent"] == agent]
    return list(bb["items"])


def clear(bb):
    bb["items"] = []
    return bb


def blackboard_health(bb):
    return {"items": len(bb["items"]), "agents": len(bb["agents"])}
