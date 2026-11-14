"""Multi-world sandbox: parallel worlds, branching, merging."""
import copy, uuid


def create_world(state=None, name="world"):
    return {"id": str(uuid.uuid4())[:6], "name": name, "state": dict(state or {}), "children": []}


def branch(world, overrides=None):
    child = create_world({**world["state"], **(overrides or {})}, name=f"{world['name']}-branch")
    world["children"].append(child["id"])
    return child


def merge(worlds, strategy="last"):
    if not worlds:
        return None
    if strategy == "last":
        return copy.deepcopy(worlds[-1])
    # union of states
    merged_state = {}
    for w in worlds:
        merged_state.update(w["state"])
    return create_world(merged_state, name="merged")


def step(world, action):
    world["state"].update(action.get("effect", {}))
    world["state"]["last_action"] = action.get("name")
    return world


def world_health(worlds):
    return {"count": len(worlds), "avg_state_keys": round(sum(len(w["state"]) for w in worlds)/max(1,len(worlds)),2)}
