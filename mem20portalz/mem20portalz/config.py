"""Portal configuration and account storage.

The config file is JSON and is expected to be stored outside the git repo
(e.g. under /opt/mem20/secrets or ~/.mem20). It contains password hashes and a
session signing secret, so it must be protected with appropriate file
permissions by the operator.
"""

from __future__ import annotations

import json
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_CONFIG_ENV = "MEM20_PORTAL_CONFIG"
DEFAULT_CONFIG_PATH = "~/.mem20/portal_accounts.json"
DEFAULT_SESSION_TTL = 12 * 3600


class ConfigError(ValueError):
    """Invalid or unusable portal configuration."""


@dataclass(frozen=True)
class UserAccount:
    username: str
    display_name: str
    password_hash: str
    store_path: str
    enabled: bool = True
    created_at: str = ""

    @property
    def resolved_store_path(self) -> str:
        return str(Path(self.store_path).expanduser())


def default_config_path() -> str:
    return os.environ.get(DEFAULT_CONFIG_ENV) or DEFAULT_CONFIG_PATH


def _expand(path: str | os.PathLike[str]) -> Path:
    return Path(path).expanduser()


def load_config(path: str | os.PathLike[str] | None = None) -> Dict[str, Any]:
    cfg_path = _expand(path or default_config_path())
    if not cfg_path.exists():
        raise ConfigError(f"config file not found: {cfg_path}")
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"config file is not valid JSON: {cfg_path}: {e}") from e
    if not isinstance(data, dict):
        raise ConfigError("config root must be a JSON object")
    data.setdefault("session_ttl_seconds", DEFAULT_SESSION_TTL)
    data.setdefault("cookie_secure", False)
    data.setdefault("users", {})
    if not isinstance(data["users"], dict):
        raise ConfigError("config.users must be an object mapping usernames to accounts")
    return data


def save_config(data: Dict[str, Any], path: str | os.PathLike[str] | None = None) -> Path:
    cfg_path = _expand(path or default_config_path())
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = cfg_path.with_suffix(cfg_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, cfg_path)
    try:
        os.chmod(cfg_path, 0o600)
    except OSError:
        pass
    return cfg_path


def new_config() -> Dict[str, Any]:
    return {
        "session_secret": secrets.token_urlsafe(48),
        "session_ttl_seconds": DEFAULT_SESSION_TTL,
        "cookie_secure": False,
        "users": {},
    }


def get_user(data: Dict[str, Any], username: str) -> Optional[UserAccount]:
    raw = (data.get("users") or {}).get(username)
    if not isinstance(raw, dict):
        return None
    store_path = str(raw.get("store_path") or "")
    if not store_path:
        return None
    return UserAccount(
        username=username,
        display_name=str(raw.get("display_name") or username),
        password_hash=str(raw.get("password_hash") or ""),
        store_path=store_path,
        enabled=bool(raw.get("enabled", True)),
        created_at=str(raw.get("created_at") or ""),
    )


def list_users(data: Dict[str, Any]) -> list[UserAccount]:
    users = []
    for name in sorted((data.get("users") or {}).keys()):
        u = get_user(data, name)
        if u:
            users.append(u)
    return users


def upsert_user(
    data: Dict[str, Any],
    username: str,
    *,
    password_hash: Optional[str] = None,
    store_path: Optional[str] = None,
    display_name: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> None:
    if not username or "/" in username or "\\" in username or username.strip() != username:
        raise ConfigError("username must be a non-empty name without slashes or surrounding whitespace")
    users = data.setdefault("users", {})
    if not isinstance(users, dict):
        raise ConfigError("config.users must be an object")
    rec = users.setdefault(username, {})
    if not isinstance(rec, dict):
        raise ConfigError(f"user record for {username!r} must be an object")
    if password_hash is not None:
        rec["password_hash"] = password_hash
    if store_path is not None:
        rec["store_path"] = str(Path(store_path).expanduser())
    if display_name is not None:
        rec["display_name"] = display_name
    elif "display_name" not in rec:
        rec["display_name"] = username
    if enabled is not None:
        rec["enabled"] = bool(enabled)
    rec.setdefault("enabled", True)
    rec.setdefault("created_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    if not rec.get("password_hash"):
        raise ConfigError(f"user {username!r} must have a password hash")
    if not rec.get("store_path"):
        raise ConfigError(f"user {username!r} must have a store_path")


def session_secret(data: Dict[str, Any]) -> str:
    secret = str(data.get("session_secret") or "")
    return secret


def session_ttl_seconds(data: Dict[str, Any]) -> int:
    try:
        ttl = int(data.get("session_ttl_seconds", DEFAULT_SESSION_TTL))
    except Exception:
        ttl = DEFAULT_SESSION_TTL
    return max(60, ttl)


def cookie_secure(data: Dict[str, Any]) -> bool:
    return bool(data.get("cookie_secure", False))
