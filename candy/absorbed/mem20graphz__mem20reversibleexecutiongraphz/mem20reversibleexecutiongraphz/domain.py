"""Reversible execution graph: execute with undo/redo."""
import copy


def create_graph():
    return {"nodes": [], "edges": [], "history": [], "cursor": -1}


def add_node(g, node):
    g["nodes"].append(node)
    g["history"].append(("add_node", node))
    g["cursor"] += 1
    return g


def undo(g):
    if g["cursor"] < 0:
        return {"ok": False}
    op, payload = g["history"][g["cursor"]]
    if op == "add_node":
        g["nodes"] = [n for n in g["nodes"] if n != payload]
    g["cursor"] -= 1
    return {"ok": True}


def redo(g):
    if g["cursor"] + 1 >= len(g["history"]):
        return {"ok": False}
    g["cursor"] += 1
    op, payload = g["history"][g["cursor"]]
    if op == "add_node":
        g["nodes"].append(payload)
    return {"ok": True}


def graph_health(g):
    return {"nodes": len(g["nodes"]), "history": len(g["history"]), "cursor": g["cursor"]}
