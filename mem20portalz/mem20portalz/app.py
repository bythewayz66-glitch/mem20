"""Customer-facing memory portal web application (aiohttp)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from aiohttp import web

from .auth import (
    SESSION_COOKIE,
    authenticate,
    clear_session_cookie,
    issue_session,
    set_session_cookie,
    verify_session,
)
from .config import ConfigError, UserAccount, get_user, load_config, session_secret
from .store import (
    StoreAccessError,
    browse_memories,
    get_entities,
    get_health,
    get_ledger,
    get_stats,
    query_memories,
    recall_memories,
)

log = logging.getLogger("mem20portalz")

STATIC_DIR = Path(__file__).resolve().parent / "web_static"
CONFIG_KEY = "portal_config"
CONFIG_PATH_KEY = "portal_config_path"


def _json(data: Any, status: int = 200) -> web.Response:
    return web.json_response(
        data,
        status=status,
        dumps=lambda obj: json.dumps(obj, ensure_ascii=False, default=str),
        headers={"Cache-Control": "no-store"},
    )


def _error(status: int, code: str, message: str) -> web.Response:
    return _json({"error": {"code": code, "message": message}}, status=status)


async def _read_json(request: web.Request) -> Optional[dict]:
    try:
        body = await request.json()
    except Exception:
        return None
    if body is None:
        return {}
    if not isinstance(body, dict):
        return None
    return body


def _cfg(request: web.Request) -> dict:
    return request.app[CONFIG_KEY]


def _current_account(request: web.Request) -> Optional[UserAccount]:
    return request.get("account")


def _safe_account_payload(account: UserAccount) -> dict:
    return {
        "username": account.username,
        "display_name": account.display_name,
    }


@web.middleware
async def auth_middleware(request: web.Request, handler):
    cfg = _cfg(request)
    token = request.cookies.get(SESSION_COOKIE)
    verified = verify_session(token, cfg)
    account = None
    if verified:
        username, _exp = verified
        account = get_user(cfg, username)
        if account and not account.enabled:
            account = None
    request["account"] = account

    path = request.path
    if path == "/api/health" or path.startswith("/api/auth/login") or path == "/api/auth/logout":
        return await handler(request)
    if path.startswith("/api/"):
        if account is None:
            return _error(401, "unauthorized", "authentication required")
        return await handler(request)
    # non-API routes (static UI) are public; UI handles auth state via API
    return await handler(request)


async def handle_health(request: web.Request) -> web.Response:
    return _json({"ok": True, "service": "mem20-portal"})


async def handle_login(request: web.Request) -> web.Response:
    cfg = _cfg(request)
    body = await _read_json(request)
    if body is None:
        return _error(400, "invalid_json", "request body must be a JSON object")
    username = str(body.get("username") or "").strip()
    password = str(body.get("password") or "")
    if not username or not password:
        return _error(400, "missing_credentials", "username and password are required")
    if not session_secret(cfg):
        return _error(503, "login_unavailable", "session_secret is not configured")
    account = get_user(cfg, username)
    if not authenticate(username, password, account):
        return _error(401, "invalid_credentials", "invalid username or password")
    assert account is not None
    try:
        token = issue_session(account.username, cfg)
    except ConfigError as e:
        return _error(503, "login_unavailable", str(e))
    resp = _json({"ok": True, "user": _safe_account_payload(account)})
    set_session_cookie(resp, token, cfg)
    return resp


async def handle_logout(request: web.Request) -> web.Response:
    resp = _json({"ok": True})
    clear_session_cookie(resp)
    return resp


async def handle_me(request: web.Request) -> web.Response:
    account = _current_account(request)
    if account is None:
        return _error(401, "unauthorized", "authentication required")
    return _json({"user": _safe_account_payload(account)})


def _int_query(request: web.Request, name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = request.rel_url.query.get(name)
    if raw is None or raw == "":
        return default
    try:
        val = int(raw)
    except Exception:
        return default
    return max(minimum, min(maximum, val))


async def handle_stats(request: web.Request) -> web.Response:
    account = _current_account(request)
    assert account is not None
    try:
        stats = await get_stats(account)
    except StoreAccessError as e:
        return _error(503, "store_unavailable", str(e))
    except Exception as e:
        log.exception("stats failed")
        return _error(500, "internal_error", "failed to read store stats")
    return _json({"stats": stats})


async def handle_mem_health(request: web.Request) -> web.Response:
    account = _current_account(request)
    assert account is not None
    try:
        health = await get_health(account)
    except StoreAccessError as e:
        return _error(503, "store_unavailable", str(e))
    except Exception:
        log.exception("health failed")
        return _error(500, "internal_error", "failed to read store health")
    return _json({"health": health})


async def handle_ledger(request: web.Request) -> web.Response:
    account = _current_account(request)
    assert account is not None
    limit = _int_query(request, "limit", 50, minimum=1, maximum=500)
    try:
        records = await get_ledger(account, limit=limit)
    except StoreAccessError as e:
        return _error(503, "store_unavailable", str(e))
    except Exception:
        log.exception("ledger failed")
        return _error(500, "internal_error", "failed to read ledger")
    return _json({"count": len(records), "records": records})


async def handle_browse(request: web.Request) -> web.Response:
    account = _current_account(request)
    assert account is not None
    limit = _int_query(request, "limit", 50, minimum=1, maximum=500)
    try:
        records = await browse_memories(account, limit=limit)
    except StoreAccessError as e:
        return _error(503, "store_unavailable", str(e))
    except Exception:
        log.exception("browse failed")
        return _error(500, "internal_error", "failed to browse memories")
    return _json({"count": len(records), "records": records})


async def handle_recall(request: web.Request) -> web.Response:
    account = _current_account(request)
    assert account is not None
    body = await _read_json(request)
    if body is None:
        return _error(400, "invalid_json", "request body must be a JSON object")
    topic = body.get("topic")
    if topic is not None and not isinstance(topic, str):
        return _error(400, "invalid_topic", "topic must be a string")
    tags = body.get("tags") or []
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        return _error(400, "invalid_tags", "tags must be a list of strings")
    k = body.get("k", 10)
    if not isinstance(k, int) or isinstance(k, bool):
        return _error(400, "invalid_k", "k must be an integer")
    try:
        records = await recall_memories(account, topic=(topic or None), tags=tags, k=k)
    except StoreAccessError as e:
        return _error(503, "store_unavailable", str(e))
    except Exception:
        log.exception("recall failed")
        return _error(500, "internal_error", "failed to recall memories")
    return _json({"count": len(records), "records": records})


async def handle_query(request: web.Request) -> web.Response:
    account = _current_account(request)
    assert account is not None
    body = await _read_json(request)
    if body is None:
        return _error(400, "invalid_json", "request body must be a JSON object")
    query = body.get("query")
    if not isinstance(query, str) or not query.strip():
        return _error(400, "invalid_query", "query must be a non-empty string")
    mode = body.get("mode", "hybrid")
    if not isinstance(mode, str) or mode.lower() not in ("semantic", "hybrid", "graph"):
        return _error(400, "invalid_mode", "mode must be one of: semantic, hybrid, graph")
    k = body.get("k", 10)
    if not isinstance(k, int) or isinstance(k, bool):
        return _error(400, "invalid_k", "k must be an integer")
    topic = body.get("topic")
    if topic is not None and not isinstance(topic, str):
        return _error(400, "invalid_topic", "topic must be a string")
    tags = body.get("tags") or []
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        return _error(400, "invalid_tags", "tags must be a list of strings")
    try:
        result = await query_memories(
            account,
            query=query.strip(),
            mode=mode.lower(),
            k=k,
            topic=(topic or None),
            tags=tags,
        )
    except StoreAccessError as e:
        return _error(503, "store_unavailable", str(e))
    except Exception:
        log.exception("query failed")
        return _error(500, "internal_error", "failed to query memories")
    return _json(result)


async def handle_entities(request: web.Request) -> web.Response:
    account = _current_account(request)
    assert account is not None
    limit = _int_query(request, "limit", 50, minimum=1, maximum=500)
    try:
        entities = await get_entities(account, limit=limit)
    except StoreAccessError as e:
        return _error(503, "store_unavailable", str(e))
    except Exception:
        log.exception("entities failed")
        return _error(500, "internal_error", "failed to read entities")
    return _json({"count": len(entities), "entities": entities})


async def handle_index(request: web.Request) -> web.StreamResponse:
    index = STATIC_DIR / "index.html"
    if not index.exists():
        return web.Response(text="mem20 portal UI not found", status=404, content_type="text/plain")
    return web.FileResponse(index, headers={"Cache-Control": "no-store"})


def create_app(config_path: Optional[str] = None) -> web.Application:
    cfg = load_config(config_path)
    app = web.Application(middlewares=[auth_middleware])
    app[CONFIG_KEY] = cfg
    app[CONFIG_PATH_KEY] = str(Path(config_path or os.environ.get("MEM20_PORTAL_CONFIG") or "~/.mem20/portal_accounts.json").expanduser())

    app.router.add_get("/api/health", handle_health)
    app.router.add_post("/api/auth/login", handle_login)
    app.router.add_post("/api/auth/logout", handle_logout)
    app.router.add_get("/api/auth/me", handle_me)
    app.router.add_get("/api/memories/stats", handle_stats)
    app.router.add_get("/api/memories/health", handle_mem_health)
    app.router.add_get("/api/memories/ledger", handle_ledger)
    app.router.add_get("/api/memories/browse", handle_browse)
    app.router.add_post("/api/memories/recall", handle_recall)
    app.router.add_post("/api/memories/query", handle_query)
    app.router.add_get("/api/memories/entities", handle_entities)

    # static assets
    if STATIC_DIR.exists():
        app.router.add_static("/static/", str(STATIC_DIR), show_index=False)
    app.router.add_get("/", handle_index)
    # SPA fallback for non-API paths
    async def spa_fallback(request: web.Request) -> web.StreamResponse:
        if request.path.startswith("/api/"):
            return _error(404, "not_found", "no such API route")
        return await handle_index(request)

    app.router.add_route("*", "/{tail:.*}", spa_fallback)
    return app


def main_run(config_path: Optional[str], host: str, port: int) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = create_app(config_path)
    web.run_app(app, host=host, port=port, print=lambda msg: log.info(msg))
