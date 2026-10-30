"""Async collaboration capsules: sessions, sync, merge, conflict resolution."""
import time, hashlib


def create_capsule(name, members=None):
    return {"name": name, "members": list(members or []), "state": {}, "log": [], "version": 0, "created_at": time.time()}


def apply_change(capsule, user, change):
    """Apply a change; bump version; log."""
    if user not in capsule["members"]:
        return {"ok": False, "error": "not a member"}
    capsule["state"].update(change)
    capsule["version"] += 1
    capsule["log"].append({"user": user, "change": change, "version": capsule["version"], "ts": time.time()})
    return {"ok": True, "version": capsule["version"]}


def sync(capsule, remote_version, remote_state):
    """Sync local with remote; return merged state and conflicts."""
    conflicts = []
    merged = dict(capsule["state"])
    for k, v in remote_state.items():
        if k in capsule["state"] and capsule["state"][k] != v:
            conflicts.append(k)
        merged[k] = v  # remote wins
    capsule["state"] = merged
    capsule["version"] = max(capsule["version"], remote_version) + 1
    return {"merged": merged, "conflicts": conflicts, "version": capsule["version"]}


def merge_capsules(c1, c2):
    """Merge two capsules into one."""
    merged = create_capsule(f"{c1['name']}+{c2['name']}", list(set(c1["members"] + c2["members"])))
    merged["state"] = {**c1["state"], **c2["state"]}
    merged["version"] = c1["version"] + c2["version"]
    merged["log"] = c1["log"] + c2["log"]
    return merged


def capsule_checksum(capsule):
    return hashlib.sha256(str(sorted(capsule["state"].items())).encode()).hexdigest()[:12]


def active_members(capsule, window=3600):
    now = time.time()
    recent = {e["user"] for e in capsule["log"] if now - e["ts"] <= window}
    return sorted(recent)
