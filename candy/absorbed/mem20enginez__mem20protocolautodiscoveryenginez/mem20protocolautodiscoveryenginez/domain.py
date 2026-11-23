"""Protocol auto-discovery engine: detect, parse, register protocols, with estate report."""
from __future__ import annotations
import re
from . import ecosystem
__all__=["detect_protocol","parse_headers","register_protocol","list_protocols","protocol_health","discovery_report","probe","estate_context"]

def detect_protocol(data):
    if isinstance(data, str):
        if data.startswith("GET ") or data.startswith("POST "): return "http"
        if "MQTT" in data.upper(): return "mqtt"
        if data.startswith("{"): return "json"
    if isinstance(data, bytes): return "binary"
    return "unknown"

def parse_headers(text):
    headers={}
    for line in text.splitlines():
        if ":" in line:
            k,v=line.split(":",1); headers[k.strip()]=v.strip()
    return headers

def register_protocol(registry, name, handler):
    registry.setdefault("protocols", {})[name] = {"handler": handler, "registered_at": __import__("time").time()}
    return registry

def list_protocols(registry):
    return list(registry.get("protocols", {}).keys())

def protocol_health(registry):
    return {"protocols": len(registry.get("protocols", {}))}

def discovery_report(data=None):
    data = data if data is not None else "GET / HTTP/1.1\nHost: x"
    proto=detect_protocol(data); headers=parse_headers(data) if isinstance(data,str) else {}; reg={}
    register_protocol(reg, proto, "handler"); health=protocol_health(reg)
    peers={
        "protocol_events": ecosystem.protocol_events("protocol.discovered", {"protocol":proto,"headers":len(headers)}),
        "handler_routing": ecosystem.handler_routing(proto, [proto,"parse"]),
        "handler_containment": ecosystem.handler_containment(proto),
        "protocol_health_check": ecosystem.protocol_health_check(list_protocols(reg)),
        "node_distribution": ecosystem.node_distribution(["n1","n2"]),
        "recovery_plans": ecosystem.recovery_plans(["redetect","fallback"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"protocol":proto,"headers":len(headers),"registered":list_protocols(reg),"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=discovery_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
