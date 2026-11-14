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

# 1st-class extensions (#336)
def plan_hibernation(models, idle_threshold=300, now=None):
    now=time.time() if now is None else now
    plan=[]
    for m in models:
        idle=now - m.get("last_activity", now)
        action="sleep" if idle>=idle_threshold and m.get("state")!="sleeping" else ("keep_awake" if m.get("state")=="awake" else "keep_sleeping")
        plan.append({"id":m.get("id"),"state":m.get("state"),"idle_s":round(idle,3),"action":action})
    return {"plan":plan,"to_sleep":[p["id"] for p in plan if p["action"]=="sleep"],"total":len(plan)}

def predictive_wake_schedule(models, demand_forecast=None):
    demand_forecast=demand_forecast or {"steps":[1,1,2]}
    steps=demand_forecast.get("steps") or demand_forecast.get("forecast") or [1]
    sleeping=[m for m in models if m.get("state")=="sleeping"]
    wake=[m.get("id") for m in sleeping[:max(1,int(sum(float(x) for x in steps if isinstance(x,(int,float)))/max(1,len(steps))))]]
    return {"demand":steps,"wake_candidates":wake,"sleeping":len(sleeping)}

def sleepwake_report(models, idle_threshold=300):
    h=plan_hibernation(models, idle_threshold=idle_threshold)
    w=predictive_wake_schedule(models)
    sh=sleep_health(models)
    return {"ok":True,"health":sh,"hibernation":h,"predictive_wake":w}
