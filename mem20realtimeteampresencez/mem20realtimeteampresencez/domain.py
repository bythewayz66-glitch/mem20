"""Real-time team presence: online/offline, locations, status."""
import time


def set_presence(presence, user, status, location=None):
    presence.setdefault("users", {})[user] = {"status": status, "location": location, "updated": time.time()}
    return presence


def get_presence(presence, user):
    return presence.get("users", {}).get(user)


def online_users(presence):
    return [u for u, info in presence.get("users", {}).items() if info.get("status") == "online"]


def away_users(presence, idle_threshold=300):
    now = time.time()
    return [u for u, info in presence.get("users", {}).items()
            if now - info.get("updated", now) > idle_threshold]


def presence_health(presence):
    users = presence.get("users", {})
    return {"total": len(users), "online": sum(1 for u in users.values() if u["status"]=="online")}
