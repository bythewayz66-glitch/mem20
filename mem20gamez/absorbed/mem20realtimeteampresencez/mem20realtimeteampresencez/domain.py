"""Real-time team presence: online/offline, locations, status, with estate report."""
from __future__ import annotations
import time
from . import ecosystem
__all__=["set_presence","get_presence","online_users","away_users","presence_health","presence_report","probe","estate_context"]

def set_presence(presence, user, status, location=None):
    presence.setdefault("users", {})[user] = {"status": status, "location": location, "updated": time.time()}
    return presence

def get_presence(presence, user):
    return presence.get("users", {}).get(user)

def online_users(presence):
    return [u for u, info in presence.get("users", {}).items() if info.get("status") == "online"]

def away_users(presence, idle_threshold=300):
    now = time.time()
    return [u for u, info in presence.get("users", {}).items() if now - info.get("updated", now) > idle_threshold]

def presence_health(presence):
    users = presence.get("users", {})
    return {"total": len(users), "online": sum(1 for u in users.values() if u["status"]=="online")}

def presence_report():
    p={}
    set_presence(p,"alice","online","hq"); set_presence(p,"bob","offline"); set_presence(p,"carol","online","remote")
    h=presence_health(p); on=online_users(p)
    peers={
        "presence_events": ecosystem.presence_events("presence.update", {"online":h["online"],"total":h["total"]}),
        "presence_routing": ecosystem.presence_routing("team", ["presence","status","location"]),
        "service_health": ecosystem.service_health(["presence","ws"]),
        "presence_containment": ecosystem.presence_containment("alice"),
        "reconnect_plans": ecosystem.reconnect_plans(["heartbeat","reconnect"]),
        "focus_context": ecosystem.focus_context({"priority":1,"distractions":0}),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"total":h["total"],"online":h["online"],"online_users":on,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=presence_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
