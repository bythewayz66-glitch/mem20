"""Autonomous work cells: task queues, worker assignment, throughput."""
import time


def create_cell(name, capacity=4):
    return {"name": name, "capacity": capacity, "queue": [], "workers": [], "completed": 0}


def enqueue(cell, task):
    cell["queue"].append(task)
    return cell


def assign_workers(cell, workers):
    cell["workers"] = workers[:cell["capacity"]]
    return cell


def process_next(cell):
    if not cell["queue"] or not cell["workers"]:
        return None
    task = cell["queue"].pop(0)
    worker = cell["workers"][cell["completed"] % len(cell["workers"])]
    cell["completed"] += 1
    return {"task": task, "worker": worker}


def throughput(cell, window_s=60):
    return round(cell["completed"] / max(1, window_s) * 60, 2)


def cell_health(cell):
    q = len(cell["queue"])
    cap = cell["capacity"]
    return {"queue_depth": q, "utilization": round(min(1.0, q / max(1, cap)), 3), "completed": cell["completed"]}
