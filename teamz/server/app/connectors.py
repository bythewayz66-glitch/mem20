from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import httpx


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


@dataclass
class ConnectorStatus:
    name: str
    configured: bool
    available: bool
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "configured": self.configured,
            "available": self.available,
            "details": self.details,
        }


# ------------------------- GitHub (REST API) -------------------------

def github_token() -> str:
    return _env("GITHUB_TOKEN") or _env("GH_TOKEN")


def github_headers(token: Optional[str] = None) -> Dict[str, str]:
    t = (token or github_token()).strip()
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "teamz-orchestrator",
    }
    if t:
        h["Authorization"] = f"Bearer {t}"
    return h


def github_status() -> ConnectorStatus:
    token = github_token()
    details: Dict[str, Any] = {"auth": "token" if token else "none"}
    if not token:
        # Unauthenticated access is still possible for some public endpoints but limited
        details["note"] = "Set GITHUB_TOKEN or GH_TOKEN for authenticated access."
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get("https://api.github.com/rate_limit", headers=github_headers(token))
            if r.status_code == 200:
                data = r.json()
                core = (data.get("resources") or {}).get("core") or {}
                details["rate_limit"] = {
                    "limit": core.get("limit"),
                    "remaining": core.get("remaining"),
                    "reset": core.get("reset"),
                }
                # Try to identify user if authenticated
                if token:
                    ur = client.get("https://api.github.com/user", headers=github_headers(token))
                    if ur.status_code == 200:
                        u = ur.json()
                        details["user"] = {"login": u.get("login"), "id": u.get("id"), "name": u.get("name")}
                    else:
                        details["user_error"] = {"status": ur.status_code, "body": ur.text[:300]}
                return ConnectorStatus("github", configured=bool(token), available=True, details=details)
            details["error"] = {"status": r.status_code, "body": r.text[:300]}
            return ConnectorStatus("github", configured=bool(token), available=r.status_code < 500, details=details)
    except Exception as e:
        details["error"] = str(e)
        return ConnectorStatus("github", configured=bool(token), available=False, details=details)


def github_request(method: str, path: str, *, token: Optional[str] = None, params: Optional[Dict[str, Any]] = None, json_body: Any = None) -> Dict[str, Any]:
    url = path
    if path.startswith("/"):
        url = "https://api.github.com" + path
    elif not path.startswith("http://") and not path.startswith("https://"):
        url = "https://api.github.com/" + path.lstrip("/")
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        r = client.request(method.upper(), url, headers=github_headers(token), params=params, json=json_body)
        ct = r.headers.get("content-type", "")
        payload: Any
        if "application/json" in ct:
            try:
                payload = r.json()
            except Exception:
                payload = r.text
        else:
            payload = r.text
        return {
            "ok": 200 <= r.status_code < 300,
            "status": r.status_code,
            "data": payload,
            "headers": {k: v for k, v in r.headers.items() if k.lower() in ("x-ratelimit-remaining", "x-ratelimit-limit", "link")},
        }


# ------------------------- GitHub CLI (gh) -------------------------

def gh_path() -> Optional[str]:
    return shutil.which("gh") or shutil.which("gh", path="/usr/bin:/usr/local/bin:/bin")


def _run(cmd: List[str], *, timeout: float = 30.0, cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            env=env or os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "ok": p.returncode == 0,
            "exit_code": p.returncode,
            "stdout": p.stdout,
            "stderr": p.stderr,
            "cmd": cmd,
        }
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "exit_code": None, "stdout": e.stdout or "", "stderr": (e.stderr or "") + "\n[timeout]", "cmd": cmd, "timeout": True}
    except Exception as e:
        return {"ok": False, "exit_code": None, "stdout": "", "stderr": str(e), "cmd": cmd}


def gh_status() -> ConnectorStatus:
    path = gh_path()
    details: Dict[str, Any] = {"path": path}
    if not path:
        details["note"] = "gh CLI not found in PATH."
        return ConnectorStatus("gh", configured=False, available=False, details=details)
    ver = _run([path, "--version"], timeout=10.0)
    details["version"] = (ver.get("stdout") or "").strip().splitlines()[0] if ver.get("stdout") else None
    auth = _run([path, "auth", "status"], timeout=15.0)
    # gh prints auth status to stderr in some versions; combine
    auth_text = ((auth.get("stdout") or "") + "\n" + (auth.get("stderr") or "")).strip()
    details["auth_status"] = {"ok": auth.get("ok"), "output": auth_text[:2000]}
    configured = bool(auth.get("ok")) or ("Logged in" in auth_text)
    details["configured_hint"] = configured
    return ConnectorStatus("gh", configured=configured, available=True, details=details)


def gh_exec(args: List[str], *, cwd: Optional[str] = None, timeout: float = 60.0) -> Dict[str, Any]:
    path = gh_path()
    if not path:
        return {"ok": False, "error": "gh CLI not found"}
    if not isinstance(args, list) or any(not isinstance(a, str) for a in args):
        return {"ok": False, "error": "args must be a list of strings"}
    # Disallow obvious shell metachar injection carriers are irrelevant since we don't use shell=True,
    # but keep command reasonable by executing argv directly.
    res = _run([path] + args, cwd=cwd, timeout=timeout)
    # Try to parse JSON if caller requested --json and stdout looks like JSON
    out = (res.get("stdout") or "").strip()
    if out.startswith("{") or out.startswith("["):
        try:
            res["json"] = json.loads(out)
        except Exception:
            pass
    return res


# ------------------------- Google -------------------------

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _load_service_account() -> Optional[Dict[str, Any]]:
    raw = _env("GOOGLE_SERVICE_ACCOUNT_JSON")
    path = _env("GOOGLE_APPLICATION_CREDENTIALS")
    if raw:
        try:
            obj = json.loads(raw)
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    if path and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    return None


def _google_access_token_from_env() -> Optional[str]:
    t = _env("GOOGLE_ACCESS_TOKEN") or _env("GOOGLE_OAUTH_ACCESS_TOKEN")
    return t or None


def _mint_google_access_token(sa: Dict[str, Any], scopes: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """Mint access token from service account using openssl for RS256 signing."""
    try:
        client_email = sa.get("client_email")
        private_key = sa.get("private_key")
        token_uri = sa.get("token_uri") or "https://oauth2.googleapis.com/token"
        if not client_email or not private_key:
            return None, "service account missing client_email/private_key"
        now = int(time.time())
        header = {"alg": "RS256", "typ": "JWT"}
        claim = {
            "iss": client_email,
            "scope": " ".join(scopes),
            "aud": token_uri,
            "iat": now,
            "exp": now + 3600,
        }
        signing_input = f"{_b64url(json.dumps(header,separators=(',',':')).encode())}.{_b64url(json.dumps(claim,separators=(',',':')).encode())}".encode("ascii")
        # Use openssl to sign
        openssl = shutil.which("openssl") or "/usr/bin/openssl"
        if not os.path.exists(openssl):
            return None, "openssl not available for service account signing"
        p = subprocess.run(
            [openssl, "dgst", "-sha256", "-sign", "/dev/stdin"],
            input=private_key.encode("utf-8") + b"\n" + b"\n" + signing_input,  # wrong: need key via stdin/file and data separately
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        return None, str(e)
    return None, "unsupported signing path"


def mint_google_access_token(scopes: Optional[List[str]] = None) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    scopes = scopes or ["https://www.googleapis.com/auth/cloud-platform"]
    meta: Dict[str, Any] = {"scopes": scopes}
    env_token = _google_access_token_from_env()
    if env_token:
        meta["source"] = "env_access_token"
        return env_token, None, meta
    sa = _load_service_account()
    if not sa:
        return None, "no_google_credentials", meta
    meta["source"] = "service_account"
    meta["client_email"] = sa.get("client_email")
    try:
        client_email = sa.get("client_email")
        private_key = sa.get("private_key")
        token_uri = sa.get("token_uri") or "https://oauth2.googleapis.com/token"
        if not client_email or not private_key:
            return None, "service_account_missing_fields", meta
        openssl = shutil.which("openssl") or "/usr/bin/openssl"
        if not os.path.exists(openssl):
            return None, "openssl_not_available", meta
        now = int(time.time())
        header = {"alg": "RS256", "typ": "JWT"}
        claim = {
            "iss": client_email,
            "scope": " ".join(scopes),
            "aud": token_uri,
            "iat": now,
            "exp": now + 3600,
        }
        import tempfile
        signing_input = _b64url(json.dumps(header, separators=(",", ":")).encode()).encode() + b"." + _b64url(json.dumps(claim, separators=(",", ":")).encode()).encode()
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".pem") as kf:
            kf.write(private_key)
            key_path = kf.name
        try:
            sig = subprocess.run(
                [openssl, "dgst", "-sha256", "-sign", key_path],
                input=signing_input,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if sig.returncode != 0:
                return None, f"openssl_sign_failed: {sig.stderr.decode('utf-8', 'replace')[:300]}", meta
            jwt = signing_input.decode() + "." + _b64url(sig.stdout)
        finally:
            try:
                os.unlink(key_path)
            except Exception:
                pass
        with httpx.Client(timeout=20.0) as client:
            r = client.post(token_uri, data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": jwt})
            if r.status_code != 200:
                return None, f"token_exchange_failed:{r.status_code}:{r.text[:300]}", meta
            data = r.json()
            token = data.get("access_token")
            if not token:
                return None, "no_access_token_in_response", meta
            meta["token_type"] = data.get("token_type")
            meta["expires_in"] = data.get("expires_in")
            return token, None, meta
    except Exception as e:
        return None, str(e), meta


def google_status() -> ConnectorStatus:
    details: Dict[str, Any] = {}
    env_token = _google_access_token_from_env()
    sa = _load_service_account()
    details["has_access_token_env"] = bool(env_token)
    details["has_service_account"] = bool(sa)
    if sa:
        details["client_email"] = sa.get("client_email")
        details["project_id"] = sa.get("project_id")
    if not env_token and not sa:
        details["note"] = "Configure GOOGLE_ACCESS_TOKEN or GOOGLE_SERVICE_ACCOUNT_JSON/GOOGLE_APPLICATION_CREDENTIALS."
        return ConnectorStatus("google", configured=False, available=False, details=details)
    token, err, meta = mint_google_access_token()
    details["token"] = meta
    if err:
        details["token_error"] = err
    # Try a lightweight API call if token obtained
    if token:
        try:
            with httpx.Client(timeout=15.0) as client:
                # tokeninfo works for many tokens; may fail for some service account tokens without scopes but worth trying
                r = client.get("https://oauth2.googleapis.com/tokeninfo", params={"access_token": token})
                if r.status_code == 200:
                    details["tokeninfo"] = r.json()
                    return ConnectorStatus("google", configured=True, available=True, details=details)
                details["tokeninfo_status"] = r.status_code
                details["tokeninfo_body"] = r.text[:300]
                # Token minted is still valid for configured scopes; treat as available
                return ConnectorStatus("google", configured=True, available=True, details=details)
        except Exception as e:
            details["probe_error"] = str(e)
            return ConnectorStatus("google", configured=True, available=True, details=details)
    return ConnectorStatus("google", configured=True, available=False, details=details)


def google_api_request(method: str, url_or_path: str, *, scopes: Optional[List[str]] = None, params: Optional[Dict[str, Any]] = None, json_body: Any = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    token, err, meta = mint_google_access_token(scopes=scopes)
    if not token:
        return {"ok": False, "error": err or "google_not_configured", "meta": meta}
    url = url_or_path
    if url_or_path.startswith("/"):
        # default to googleapis base when path-like
        url = "https://www.googleapis.com" + url_or_path
    req_headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        r = client.request(method.upper(), url, headers=req_headers, params=params, json=json_body)
        ct = r.headers.get("content-type", "")
        payload: Any
        if "application/json" in ct:
            try:
                payload = r.json()
            except Exception:
                payload = r.text
        else:
            payload = r.text
        return {"ok": 200 <= r.status_code < 300, "status": r.status_code, "data": payload, "meta": meta}


def connectors_status() -> Dict[str, Any]:
    return {
        "github": github_status().to_dict(),
        "gh": gh_status().to_dict(),
        "google": google_status().to_dict(),
    }
