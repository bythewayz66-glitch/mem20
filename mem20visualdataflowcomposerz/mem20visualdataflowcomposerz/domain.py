"""Visual dataflow composer: compose dataflow pipelines visually."""
import uuid


def create_pipeline(name):
    return {"name": name, "nodes": [], "edges": []}


def add_node(pipeline, node_type, config=None):
    node = {"id": str(uuid.uuid4())[:6], "type": node_type, "config": config or {}}
    pipeline["nodes"].append(node)
    return node


def connect(pipeline, from_id, to_id):
    pipeline["edges"].append({"from": from_id, "to": to_id})
    return pipeline


def execute(pipeline, data, runner):
    # topological-ish: just run nodes in order
    results = {}
    for n in pipeline["nodes"]:
        results[n["id"]] = runner(n, data)
    return results


def pipeline_health(pipeline):
    return {"nodes": len(pipeline["nodes"]), "edges": len(pipeline["edges"])}
