"""Persistent workspace/session storage.

The workspace (agents, channels, messages, goals, tasks, activity) is written to
a single JSON file atomically so it survives browser restarts and server
restarts. Writes go to a temp file in the same directory and are ``os.replace``d
into place, so a crash mid-write can never leave a half-written state file.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional


STATE_VERSION = 1


def empty_state() -> Dict[str, Any]:
    return {
        "version": STATE_VERSION,
        "updatedAt": int(time.time() * 1000),
        "agents": [],
        "conversations": [],
        "messages": {},
        "filters": {},
        "activeConversationId": None,
        "goals": {},
        "tasks": [],
        "activity": [],
    }


def normalize_state(raw: Any) -> Dict[str, Any]:
    """Coerce an arbitrary persisted blob into a complete state dict."""
    base = empty_state()
    if not isinstance(raw, dict):
        return base
    out = dict(base)
    for key in ("version", "updatedAt", "activeConversationId"):
        if key in raw:
            out[key] = raw[key]
    if isinstance(raw.get("agents"), list):
        out["agents"] = raw["agents"]
    if isinstance(raw.get("conversations"), list):
        out["conversations"] = raw["conversations"]
    if isinstance(raw.get("messages"), dict):
        out["messages"] = raw["messages"]
    if isinstance(raw.get("filters"), dict):
        out["filters"] = raw["filters"]
    if isinstance(raw.get("goals"), dict):
        out["goals"] = raw["goals"]
    if isinstance(raw.get("tasks"), list):
        out["tasks"] = raw["tasks"]
    if isinstance(raw.get("activity"), list):
        out["activity"] = raw["activity"]
    return out


class StateStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path).expanduser().resolve()
        self._lock = threading.RLock()

    def exists(self) -> bool:
        return self.path.is_file() and self.path.stat().st_size > 0

    def load(self) -> Dict[str, Any]:
        with self._lock:
            if not self.exists():
                return empty_state()
            try:
                with self.path.open("r", encoding="utf-8") as f:
                    raw = json.load(f)
            except (json.JSONDecodeError, OSError):
                # A corrupt file should not brick the server: fall back to the
                # last good snapshot if one exists, else start empty.
                backup = self.path.with_suffix(self.path.suffix + ".bak")
                if backup.is_file():
                    try:
                        with backup.open("r", encoding="utf-8") as f:
                            raw = json.load(f)
                    except Exception:
                        return empty_state()
                else:
                    return empty_state()
            return normalize_state(raw)

    def save(self, state: Dict[str, Any]) -> None:
        with self._lock:
            payload = normalize_state(state)
            payload["version"] = STATE_VERSION
            payload["updatedAt"] = int(time.time() * 1000)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(
                prefix=self.path.name + ".", suffix=".tmp", dir=str(self.path.parent)
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                # Keep the previous good file as a backup, then swap atomically.
                if self.path.exists():
                    try:
                        os.replace(self.path, self.path.with_suffix(self.path.suffix + ".bak"))
                    except OSError:
                        pass
                os.replace(tmp_name, self.path)
            finally:
                if os.path.exists(tmp_name):
                    try:
                        os.unlink(tmp_name)
                    except OSError:
                        pass

    def summary(self) -> Dict[str, Any]:
        state = self.load()
        return {
            "path": str(self.path),
            "enabled": True,
            "exists": self.exists(),
            "updatedAt": state.get("updatedAt"),
            "agents": len(state.get("agents") or []),
            "conversations": len(state.get("conversations") or []),
            "goals": len(state.get("goals") or {}),
            "activity": len(state.get("activity") or []),
        }
