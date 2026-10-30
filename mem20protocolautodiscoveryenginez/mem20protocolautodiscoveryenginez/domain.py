"""Protocol auto-discovery engine: detect, parse, register protocols."""
import re


def detect_protocol(data):
    if isinstance(data, str):
        if data.startswith("GET ") or data.startswith("POST "):
            return "http"
        if "MQTT" in data.upper():
            return "mqtt"
        if data.startswith("{"):
            return "json"
    if isinstance(data, bytes):
        return "binary"
    return "unknown"


def parse_headers(text):
    headers = {}
    for line in text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip()] = v.strip()
    return headers


def register_protocol(registry, name, handler):
    registry.setdefault("protocols", {})[name] = {"handler": handler, "registered_at": __import__("time").time()}
    return registry


def list_protocols(registry):
    return list(registry.get("protocols", {}).keys())


def protocol_health(registry):
    return {"protocols": len(registry.get("protocols", {}))}
