"""Ambient team radio: channel management, presence, message routing."""
import time


def create_channel(name, members=None):
    return {"name": name, "members": list(members or []), "messages": [], "created_at": time.time()}


def join_channel(channel, user):
    if user not in channel["members"]:
        channel["members"].append(user)
    return channel


def leave_channel(channel, user):
    channel["members"] = [m for m in channel["members"] if m != user]
    return channel


def send_message(channel, user, text):
    if user not in channel["members"]:
        return {"ok": False, "error": "not a member"}
    msg = {"user": user, "text": text, "ts": time.time()}
    channel["messages"].append(msg)
    return {"ok": True, "message": msg}


def channel_activity(channel, window=3600):
    now = time.time()
    recent = [m for m in channel["messages"] if now - m["ts"] <= window]
    return {"recent_count": len(recent), "active_members": len({m["user"] for m in recent})}


def route_message(channels, user, text):
    """Route a message to all channels the user is in."""
    delivered = []
    for c in channels:
        if user in c.get("members", []):
            send_message(c, user, text)
            delivered.append(c["name"])
    return delivered
