"""Model sleep/wake system: idle detection, hibernation, wake triggers."""
import time


def track_activity(model, activity_ts=None):
    model["last_activity"] = time.time() if activity_ts is None else activity_ts
    model["state"] = "awake"
    return model


def should_sleep(model, idle_threshold=300):
    idle = time.time() - model.get("last_activity", time.time())
    return idle >= idle_threshold


def sleep(model):
    model["state"] = "sleeping"
    model["slept_at"] = time.time()
    return model


def wake(model, trigger="manual"):
    model["state"] = "awake"
    model["last_activity"] = time.time()
    model["wake_trigger"] = trigger
    return model


def sleep_health(models):
    sleeping = sum(1 for m in models if m.get("state") == "sleeping")
    return {"total": len(models), "sleeping": sleeping, "awake": len(models)-sleeping}
