"""Autonomous software foundry: spec to code, test, deploy."""
import hashlib


def spec_to_tasks(spec):
    tasks = []
    for f in spec.get("features", []):
        tasks.append({"id": f"task-{f}", "feature": f, "status": "todo"})
    tasks.append({"id": "tests", "feature": "test suite", "status": "todo"})
    tasks.append({"id": "deploy", "feature": "deployment", "status": "todo"})
    return tasks


def code_quality(metrics):
    score = 0.0
    if metrics.get("tests_pass"):
        score += 0.4
    if metrics.get("coverage", 0) >= 0.8:
        score += 0.3
    if metrics.get("lint_clean"):
        score += 0.3
    return round(score, 3)


def deploy_decision(quality, threshold=0.7):
    return quality >= threshold


def estimate_effort(spec):
    base = len(spec.get("features", [])) * 2
    return {"days": base, "complexity": "high" if base > 10 else "medium" if base > 4 else "low"}


def build_artifact(spec, code):
    return {"name": spec.get("name"), "version": "0.1.0", "checksum": hashlib.sha256(code.encode()).hexdigest()[:12], "size_lines": code.count(chr(10))}
