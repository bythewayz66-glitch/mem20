"""Self-healing runtime civilization: multi-agent self-repair ecosystem."""
import time


def create_civilization(agents):
    return {"agents": {a: {"health": 1.0, "status": "alive"} for a in agents}, "repairs": []}


def damage(civ, agent, amount):
    if agent in civ["agents"]:
        civ["agents"][agent]["health"] = max(0, civ["agents"][agent]["health"] - amount)
        if civ["agents"][agent]["health"] == 0:
            civ["agents"][agent]["status"] = "dead"
    return civ


def heal(civ, agent, amount):
    if agent in civ["agents"]:
        civ["agents"][agent]["health"] = min(1.0, civ["agents"][agent]["health"] + amount)
        if civ["agents"][agent]["health"] > 0:
            civ["agents"][agent]["status"] = "alive"
        civ["repairs"].append({"agent": agent, "amount": amount, "ts": time.time()})
    return civ


def auto_heal(civ, threshold=0.3, amount=0.5):
    for a, info in civ["agents"].items():
        if info["health"] < threshold:
            heal(civ, a, amount)
    return civ


def civ_health(civ):
    alive = sum(1 for a in civ["agents"].values() if a["status"]=="alive")
    return {"agents": len(civ["agents"]), "alive": alive, "avg_health": round(sum(a["health"] for a in civ["agents"].values())/max(1,len(civ["agents"])),4)}
