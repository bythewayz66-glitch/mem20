"""Living agent economy: agents earn/spend, trade, reputation."""
import math


def create_economy(agents=None):
    return {"agents": {a: {"balance": 100, "reputation": 0.5, "skills": []} for a in (agents or [])}, "transactions": []}


def earn(econ, agent, amount, reason=""):
    if agent not in econ["agents"]:
        econ["agents"][agent] = {"balance": 0, "reputation": 0.5, "skills": []}
    econ["agents"][agent]["balance"] += amount
    econ["transactions"].append({"type": "earn", "agent": agent, "amount": amount, "reason": reason})
    return econ


def spend(econ, agent, amount, reason=""):
    if econ["agents"].get(agent, {}).get("balance", 0) < amount:
        return {"ok": False, "reason": "insufficient"}
    econ["agents"][agent]["balance"] -= amount
    econ["transactions"].append({"type": "spend", "agent": agent, "amount": amount, "reason": reason})
    return {"ok": True}


def trade(econ, a, b, amount):
    if spend(econ, a, amount, "trade")["ok"]:
        earn(econ, b, amount, "trade")
        return {"ok": True}
    return {"ok": False}


def reputation(econ, agent):
    return econ["agents"].get(agent, {}).get("reputation", 0)
