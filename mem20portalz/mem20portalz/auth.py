"""Authentication: password hashing and signed session cookies.

Passwords are hashed with PBKDF2-HMAC-SHA256. Session tokens are HMAC-SHA256
signed and time-limited. All comparisons involving secrets use constant-time
checks. Missing configuration fails closed.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from typing import Optional, Tuple

from aiohttp import web

from .config import ConfigError, UserAccount, cookie_secure, session_secret, session_ttl_seconds

PBKDF2_ALGO = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 390_000
PBKDF2_SALT_BYTES = 16
PBKDF2_HASH_BYTES = 32
SESSION_COOKIE = "mem20_portal_session"


def hash_password(password: str, *, iterations: int = PBKDF2_ITERATIONS) -> str:
    if password is None or password == "":
        raise ConfigError("password must not be empty")
    salt = os.urandom(PBKDF2_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=PBKDF2_HASH_BYTES)
    return "{}${}${}${}".format(
        PBKDF2_ALGO,
        iterations,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(dk).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iters_s, salt_b64, hash_b64 = str(encoded).split("$", 3)
        if algo != PBKDF2_ALGO:
            return False
        iterations = int(iters_s)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(hash_b64.encode("ascii"))
    except Exception:
        return False
    if iterations <= 0 or not salt or not expected:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", (password or "").encode("utf-8"), salt, iterations, dklen=len(expected))
    return hmac.compare_digest(dk, expected)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode((text + pad).encode("ascii"))


def issue_session(username: str, cfg: dict) -> str:
    secret = session_secret(cfg)
    if not secret:
        raise ConfigError("session_secret is not configured; login is disabled")
    exp = int(time.time()) + session_ttl_seconds(cfg)
    payload = f"{_b64url_encode(username.encode('utf-8'))}.{exp}"
    sig = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return f"{payload}.{_b64url_encode(sig)}"


def verify_session(token: Optional[str], cfg: dict) -> Optional[Tuple[str, int]]:
    secret = session_secret(cfg)
    if not secret or not token:
        return None
    parts = str(token).split(".")
    if len(parts) != 3:
        return None
    u_b64, exp_s, sig_b64 = parts
    payload = f"{u_b64}.{exp_s}"
    try:
        expected = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
        got = _b64url_decode(sig_b64)
        if not hmac.compare_digest(got, expected):
            return None
        exp = int(exp_s)
        if exp <= int(time.time()):
            return None
        username = _b64url_decode(u_b64).decode("utf-8")
    except Exception:
        return None
    if not username:
        return None
    return username, exp


def set_session_cookie(response: web.StreamResponse, token: str, cfg: dict) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=session_ttl_seconds(cfg),
        httponly=True,
        samesite="Lax",
        secure=cookie_secure(cfg),
        path="/",
    )


def clear_session_cookie(response: web.StreamResponse) -> None:
    response.del_cookie(SESSION_COOKIE, path="/")


def authenticate(username: str, password: str, account: Optional[UserAccount]) -> bool:
    if account is None or not account.enabled:
        # perform a dummy hash comparison path to reduce trivial timing differences
        verify_password(password or "", hash_password("dummy-password-for-timing"))
        return False
    if not account.password_hash:
        return False
    return verify_password(password or "", account.password_hash)