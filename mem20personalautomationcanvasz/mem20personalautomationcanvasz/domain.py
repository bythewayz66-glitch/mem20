"""Personal automation canvas: workflows, triggers, actions."""
import time, uuid


def create_canvas(name, owner):
    return {"name": name, "owner": owner, "workflows": [], "triggers": []}


def add_workflow(canvas, workflow):
    canvas["workflows"].append({"id": str(uuid.uuid4())[:6], **workflow, "enabled": True})
    return canvas


def add_trigger(canvas, trigger):
    canvas["triggers"].append(trigger)
    return canvas


def run_workflow(wf, context):
    return {"workflow": wf.get("name"), "status": "completed", "steps": wf.get("steps", []), "context": context, "ran_at": time.time()}


def canvas_health(canvas):
    return {"workflows": len(canvas["workflows"]), "triggers": len(canvas["triggers"]), "enabled": sum(1 for w in canvas["workflows"] if w.get("enabled"))}
