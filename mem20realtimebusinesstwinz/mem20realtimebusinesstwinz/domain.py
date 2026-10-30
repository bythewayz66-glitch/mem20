"""Real-time business twin: live KPIs, scenarios, alerts."""
import time


def create_twin(business):
    return {"business": business, "kpis": {}, "alerts": [], "updated": time.time()}


def update_kpi(twin, kpi, value):
    twin["kpis"][kpi] = value
    twin["updated"] = time.time()
    return twin


def check_alerts(twin, thresholds):
    alerts = []
    for kpi, thr in thresholds.items():
        val = twin["kpis"].get(kpi)
        if val is not None and val > thr:
            alerts.append({"kpi": kpi, "value": val, "threshold": thr})
    twin["alerts"] = alerts
    return alerts


def scenario(twin, changes):
    new_kpis = dict(twin["kpis"])
    new_kpis.update(changes)
    return {"kpis": new_kpis, "delta": {k: new_kpis[k]-twin["kpis"].get(k,0) for k in changes}}


def twin_health(twin):
    return {"kpis": len(twin["kpis"]), "alerts": len(twin["alerts"]), "fresh": time.time()-twin["updated"] < 60}
