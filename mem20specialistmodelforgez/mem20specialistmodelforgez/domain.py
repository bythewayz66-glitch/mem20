"""Specialist model forge: create fine-tuned specialist models."""
import random


def forge(base_model, specialty, data, seed=0):
    rng = random.Random(seed)
    params = {f"w{i}": rng.random() for i in range(4)}
    return {"name": f"{base_model}-{specialty}", "base": base_model, "specialty": specialty, "params": params, "trained_on": len(data)}


def evaluate(model, test_data):
    # mock accuracy
    return round(0.7 + 0.01*len(test_data)*0.0, 4) if test_data else 0.5


def merge_specialists(models):
    # average params
    if not models:
        return None
    keys = models[0]["params"].keys()
    merged = {k: sum(m["params"].get(k, 0) for m in models)/len(models) for k in keys}
    return {"name": "merged", "params": merged, "specialties": [m["specialty"] for m in models]}


def forge_health(models):
    return {"models": len(models), "specialties": len(set(m["specialty"] for m in models))}
