"""Real-time business twin: live KPIs, scenarios, alerts, with estate report."""
from __future__ import annotations
import time
from . import ecosystem
__all__=["create_twin","update_kpi","check_alerts","scenario","twin_health","business_twin_report","probe","estate_context"]

def create_twin(business):
    return {"business": business, "kpis": {}, "alerts": [], "updated": time.time()}

def update_kpi(twin, kpi, value):
    twin["kpis"][kpi] = value; twin["updated"] = time.time(); return twin

def check_alerts(twin, thresholds):
    alerts=[]
    for kpi, thr in thresholds.items():
        val=twin["kpis"].get(kpi)
        if val is not None and val > thr: alerts.append({"kpi": kpi, "value": val, "threshold": thr})
    twin["alerts"]=alerts; return alerts

def scenario(twin, changes):
    new_kpis=dict(twin["kpis"]); new_kpis.update(changes)
    return {"kpis": new_kpis, "delta": {k: new_kpis[k]-twin["kpis"].get(k,0) for k in changes}}

def twin_health(twin):
    return {"kpis": len(twin["kpis"]), "alerts": len(twin["alerts"]), "fresh": time.time()-twin["updated"] < 60}

def business_twin_report(business="acme"):
    twin=create_twin(business); update_kpi(twin,"revenue",120); update_kpi(twin,"churn",0.15)
    alerts=check_alerts(twin,{"churn":0.1}); scen=scenario(twin,{"revenue":140}); health=twin_health(twin)
    peers={
        "business_scenarios": ecosystem.business_scenarios(twin["kpis"].get("revenue",0)),
        "kpi_forecast": ecosystem.kpi_forecast([100,110,120]),
        "kpi_events": ecosystem.kpi_events("twin.report", {"business":business,"alerts":len(alerts)}),
        "health_alerts": ecosystem.health_alerts(["revenue","churn"]),
        "counterfactual_scenarios": ecosystem.counterfactual_scenarios({"revenue":twin["kpis"].get("revenue",0)}),
        "capability_routing": ecosystem.capability_routing(business, ["monitor","alert","scenario"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"kpis":twin["kpis"],"alerts":len(alerts),"scenario_delta":scen["delta"],"health":health,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=business_twin_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
