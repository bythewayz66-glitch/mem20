"""Intent to mission compiler: decompose intent into mission steps."""
import uuid


def compile_mission(intent):
    steps = []
    # decompose
    for part in intent.get("parts", [intent.get("goal", "")]):
        steps.append({"id": str(uuid.uuid4())[:6], "action": part, "status": "pending"})
    if not steps:
        steps.append({"id": str(uuid.uuid4())[:6], "action": intent.get("goal", "execute"), "status": "pending"})
    return {"mission_id": str(uuid.uuid4())[:8], "intent": intent, "steps": steps, "status": "planned"}


def assign_agents(mission, agents):
    for i, step in enumerate(mission["steps"]):
        step["agent"] = agents[i % len(agents)] if agents else None
    return mission


def mission_progress(mission):
    done = sum(1 for s in mission["steps"] if s.get("status") == "done")
    total = len(mission["steps"])
    return {"done": done, "total": total, "progress": round(done / max(1, total), 4)}


def validate_mission(mission):
    return len(mission.get("steps", [])) > 0


def execute_step(mission, step_id):
    for s in mission["steps"]:
        if s["id"] == step_id:
            s["status"] = "done"
    return mission
