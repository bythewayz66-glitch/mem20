"""Remote experiment lab: run experiments on remote nodes."""
import time, uuid


def create_experiment(name, params):
    return {"id": str(uuid.uuid4())[:8], "name": name, "params": params, "status": "created", "results": None}


def run(experiment, runner):
    experiment["status"] = "running"
    res = runner(experiment["params"])
    experiment["results"] = res
    experiment["status"] = "completed"
    experiment["finished"] = time.time()
    return experiment


def compare(experiments):
    return sorted(experiments, key=lambda e: -(e.get("results", {}) or {}).get("score", 0))


def experiment_health(experiments):
    done = sum(1 for e in experiments if e.get("status") == "completed")
    return {"total": len(experiments), "completed": done}
