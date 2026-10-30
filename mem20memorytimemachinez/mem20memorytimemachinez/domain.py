"""Memory time machine: snapshot, rewind, replay, diff."""
import copy, time


def snapshot(state, label=""):
    return {"label": label, "state": copy.deepcopy(state), "ts": time.time()}


def rewind(snapshots, index):
    if 0 <= index < len(snapshots):
        return copy.deepcopy(snapshots[index]["state"])
    return None


def replay(snapshots):
    return [s["state"] for s in snapshots]


def diff(a, b):
    diffs = {}
    for k in set(a) | set(b):
        if a.get(k) != b.get(k):
            diffs[k] = {"from": a.get(k), "to": b.get(k)}
    return diffs


def timeline(snapshots):
    return [{"label": s["label"], "ts": s["ts"]} for s in snapshots]
