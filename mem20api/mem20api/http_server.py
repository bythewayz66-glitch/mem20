"""mem20 HTTP/JSON service — the 4.0 server lane's read surface.

Why this exists
---------------
`bridge/server.py` is the only HTTP surface in the tree and it imports
FastAPI, uvicorn and httpx. None of those are installed on a stock host, so the
service cannot start from a clean checkout, and a failed import is
indistinguishable from a crashed process to anything watching the port.

This module is the supported HTTP entry point instead:

* **Standard library only.** `http.server` + `json`. A `git clone --depth 1`
  checkout serves requests with no `pip install` at all.
* **Fail-closed by default.** With no `MEM20_API_TOKEN` the service refuses to
  bind a non-loopback address. It will not expose a memory store to a network
  because someone forgot to set a variable.
* **Honest status codes.** `/readyz` is 503 when the store's indexes have
  drifted, not 200 with a `healthy: false` body that a load balancer ignores.
* **One store, one lock.** The engine resolves its paths as module globals, so
  two threads inside one store can rebind each other's paths. Every store call
  is serialised through a single lock; the HTTP layer is threaded, the engine
  access is not.

Endpoints
---------
    GET  /healthz                 liveness; never touches the store
    GET  /readyz                  readiness; 200 healthy / 503 drifted
    GET  /v1/stats                record and topic counts
    GET  /v1/ledger?k=20          most recent ledger events
    GET  /v1/entities?limit=50    graph entities, most connected first
    POST /v1/recall               {"topic": ..., "tags": [...], "k": 5}
    POST /v1/query                {"query": ..., "mode": "hybrid", "k": 5}

Run it
------
    python -m mem20api.http_server --store "$HOME/.mem20/store" --port 8099

    # one-shot readiness probe, for a systemd ExecStartPre or a container check
    python -m mem20api.http_server --check --store "$HOME/.mem20/store"

Environment
-----------
    MEM20_STORE_PATH   default store when --store is not given
    MEM20_API_TOKEN    bearer token required on every /v1/* and /readyz call
    MEM20_API_HOST     default bind host (127.0.0.1)
    MEM20_API_PORT     default bind port (8099)
"""
from __future__ import annotations

import argparse
import hmac
import json
import os
import sys
import threading
import time
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from .api import EngineNotFound, StoreError, open_store

__all__ = ["ApiServer", "make_server", "main", "API_VERSION"]

API_VERSION = "1"
SERVICE_NAME = "mem20-api"

#: A request body larger than this is refused rather than buffered. Recall and
#: query payloads are a few hundred bytes; anything bigger is a mistake or an
#: attempt to exhaust memory.
MAX_BODY_BYTES = 64 * 1024

#: Hosts that are not reachable from another machine. Binding one of these
#: without a token is allowed; binding anything else is not.
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost", ""})

#: Paths that never require a token. Liveness must answer before the store is
#: open, otherwise a supervisor cannot tell "starting" from "dead".
PUBLIC_PATHS = frozenset({"/healthz"})


class ConfigError(RuntimeError):
    """The service was asked to start in an unsafe or impossible configuration."""


def _is_loopback(host: str) -> bool:
    return host in LOOPBACK_HOSTS or host.startswith("127.")


class ApiServer(ThreadingHTTPServer):
    """ThreadingHTTPServer carrying the store, the token and the lock.

    The store is opened once at startup and shared by every request thread.
    `store_lock` is what makes that safe: the engine rebinds module-level path
    globals on every call, so concurrent calls would otherwise write to each
    other's store.
    """

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], store_path: str,
                 token: str | None = None) -> None:
        self.store_path = store_path
        self.token = token
        self.store_lock = threading.Lock()
        self.started_at = time.time()
        self._store = None
        super().__init__(address, ApiHandler)

    # -- store lifecycle -------------------------------------------------

    def open_store(self):
        """Open the store once. Raises StoreError/EngineNotFound on failure."""
        if self._store is None:
            self._store = open_store(self.store_path)
        return self._store

    def close_store(self) -> None:
        store, self._store = self._store, None
        if store is not None:
            try:
                store.__exit__(None, None, None)
            except Exception:  # pragma: no cover - best effort on shutdown
                pass

    def server_close(self) -> None:
        self.close_store()
        super().server_close()

    # -- helpers ---------------------------------------------------------

    def uptime(self) -> float:
        return round(time.time() - self.started_at, 3)


class ApiHandler(BaseHTTPRequestHandler):
    """One request. Every response is JSON, including every error."""

    server_version = f"{SERVICE_NAME}/{API_VERSION}"
    sys_version = ""

    # -- plumbing --------------------------------------------------------

    def log_message(self, fmt: str, *args: Any) -> None:
        """Emit one JSON line per request instead of the default text log."""
        sys.stderr.write(json.dumps({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "service": SERVICE_NAME,
            "client": self.client_address[0] if self.client_address else None,
            "message": fmt % args,
        }) + "\n")

    def _request_id(self) -> str:
        return uuid.uuid4().hex[:16]

    def _send_json(self, status: int, payload: dict, request_id: str) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Request-Id", request_id)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _error(self, status: int, code: str, message: str,
               request_id: str) -> None:
        self._send_json(status, {
            "error": {"code": code, "message": message},
            "request_id": request_id,
        }, request_id)

    def _read_json_body(self, request_id: str) -> dict | None:
        """Parse a JSON object body, or answer 400/413 and return None."""
        raw_len = self.headers.get("Content-Length")
        if raw_len is None:
            self._error(HTTPStatus.LENGTH_REQUIRED, "length_required",
                        "a JSON body with Content-Length is required",
                        request_id)
            return None
        try:
            length = int(raw_len)
        except ValueError:
            self._error(HTTPStatus.BAD_REQUEST, "bad_length",
                        "Content-Length is not an integer", request_id)
            return None
        if length < 0 or length > MAX_BODY_BYTES:
            self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "body_too_large",
                        f"body must be 0..{MAX_BODY_BYTES} bytes", request_id)
            return None
        raw = self.rfile.read(length) if length else b""
        if not raw:
            return {}
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            self._error(HTTPStatus.BAD_REQUEST, "invalid_json",
                        f"body is not valid JSON: {e}", request_id)
            return None
        if not isinstance(parsed, dict):
            self._error(HTTPStatus.BAD_REQUEST, "invalid_body",
                        "body must be a JSON object", request_id)
            return None
        return parsed

    def _authorised(self, path: str) -> bool:
        """True when this request may proceed.

        `/healthz` is always open. Everything else needs the bearer token when
        one is configured. When no token is configured the server can only be
        bound to loopback (enforced in make_server), so the request is local.
        """
        if path in PUBLIC_PATHS:
            return True
        token = getattr(self.server, "token", None)
        if not token:
            return True
        header = self.headers.get("Authorization", "")
        scheme, _, presented = header.partition(" ")
        if scheme.lower() != "bearer" or not presented:
            return False
        return hmac.compare_digest(presented.strip(), token)

    # -- dispatch --------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        self._dispatch("GET")

    def do_HEAD(self) -> None:  # noqa: N802
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

    def _dispatch(self, method: str) -> None:
        request_id = self._request_id()
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)

        if not self._authorised(path):
            self._error(HTTPStatus.UNAUTHORIZED, "unauthorised",
                        "a valid bearer token is required", request_id)
            return

        routes: dict[str, tuple[str, Any]] = {
            "/healthz": ("GET", self._handle_healthz),
            "/readyz": ("GET", self._handle_readyz),
            "/v1/stats": ("GET", self._handle_stats),
            "/v1/ledger": ("GET", self._handle_ledger),
            "/v1/entities": ("GET", self._handle_entities),
            "/v1/recall": ("POST", self._handle_recall),
            "/v1/query": ("POST", self._handle_query),
        }
        route = routes.get(path)
        if route is None:
            self._error(HTTPStatus.NOT_FOUND, "not_found",
                        f"no route for {path}", request_id)
            return
        allowed, handler = route
        if method != allowed:
            self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
            self.send_header("Allow", allowed)
            body = json.dumps({
                "error": {"code": "method_not_allowed",
                          "message": f"{path} accepts {allowed}"},
                "request_id": request_id,
            }).encode("utf-8")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Request-Id", request_id)
            self.end_headers()
            self.wfile.write(body)
            return

        try:
            handler(query, request_id)
        except (EngineNotFound, StoreError) as e:
            self._error(HTTPStatus.SERVICE_UNAVAILABLE, "store_unavailable",
                        str(e), request_id)
        except Exception as e:  # noqa: BLE001 - never leak a traceback
            self.log_message("unhandled error on %s: %r", path, e)
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error",
                        "the request failed; see the service log for the "
                        "request id", request_id)

    # -- handlers --------------------------------------------------------

    def _handle_healthz(self, query: dict, request_id: str) -> None:
        self._send_json(HTTPStatus.OK, {
            "status": "ok",
            "service": SERVICE_NAME,
            "api_version": API_VERSION,
            "uptime_s": self.server.uptime(),
            "request_id": request_id,
        }, request_id)

    def _handle_readyz(self, query: dict, request_id: str) -> None:
        with self.server.store_lock:
            health = self.server.open_store().health()
        healthy = bool(health.get("healthy"))
        self._send_json(
            HTTPStatus.OK if healthy else HTTPStatus.SERVICE_UNAVAILABLE,
            {
                "status": "ready" if healthy else "drifted",
                "store": health.get("store"),
                "ledger_records": health.get("ledger_records"),
                "indexes": health.get("indexes"),
                "request_id": request_id,
            }, request_id)

    def _handle_stats(self, query: dict, request_id: str) -> None:
        with self.server.store_lock:
            stats = self.server.open_store().stats()
        stats.pop("health", None)
        stats["request_id"] = request_id
        self._send_json(HTTPStatus.OK, stats, request_id)

    def _handle_ledger(self, query: dict, request_id: str) -> None:
        k = _int_param(query, "k", 20, minimum=1, maximum=500)
        with self.server.store_lock:
            records = self.server.open_store().ledger(k=k)
        self._send_json(HTTPStatus.OK, {
            "count": len(records),
            "records": records,
            "request_id": request_id,
        }, request_id)

    def _handle_entities(self, query: dict, request_id: str) -> None:
        limit = _int_param(query, "limit", 50, minimum=1, maximum=500)
        with self.server.store_lock:
            entities = self.server.open_store().entities(limit=limit)
        self._send_json(HTTPStatus.OK, {
            "count": len(entities),
            "entities": entities,
            "request_id": request_id,
        }, request_id)

    def _handle_recall(self, query: dict, request_id: str) -> None:
        body = self._read_json_body(request_id)
        if body is None:
            return
        topic = body.get("topic")
        if topic is not None and not isinstance(topic, str):
            self._error(HTTPStatus.BAD_REQUEST, "invalid_topic",
                        "topic must be a string", request_id)
            return
        tags = body.get("tags") or []
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            self._error(HTTPStatus.BAD_REQUEST, "invalid_tags",
                        "tags must be a list of strings", request_id)
            return
        k = body.get("k", 5)
        if not isinstance(k, int) or isinstance(k, bool) or not 1 <= k <= 500:
            self._error(HTTPStatus.BAD_REQUEST, "invalid_k",
                        "k must be an integer in 1..500", request_id)
            return
        with self.server.store_lock:
            hits = self.server.open_store().recall(topic=topic, tags=tags, k=k)
        self._send_json(HTTPStatus.OK, {
            "count": len(hits),
            "hits": hits,
            "request_id": request_id,
        }, request_id)

    def _handle_query(self, query: dict, request_id: str) -> None:
        body = self._read_json_body(request_id)
        if body is None:
            return
        text = body.get("query")
        if not isinstance(text, str) or not text.strip():
            self._error(HTTPStatus.BAD_REQUEST, "invalid_query",
                        "query must be a non-empty string", request_id)
            return
        mode = body.get("mode", "hybrid")
        if mode not in ("semantic", "hybrid", "graph"):
            self._error(HTTPStatus.BAD_REQUEST, "invalid_mode",
                        "mode must be one of semantic, hybrid, graph",
                        request_id)
            return
        k = body.get("k", 5)
        if not isinstance(k, int) or isinstance(k, bool) or not 1 <= k <= 50:
            self._error(HTTPStatus.BAD_REQUEST, "invalid_k",
                        "k must be an integer in 1..50", request_id)
            return

        with self.server.store_lock:
            store = self.server.open_store()
            if mode == "semantic":
                result = store.semantic(text, k=k)
                payload = {
                    "mode": mode,
                    "hits": result["hits"],
                    "diagnostic": result["diagnostic"],
                    "healthy": result["healthy"],
                }
            elif mode == "hybrid":
                result = store.hybrid(text, k=k)
                payload = {
                    "mode": mode,
                    "hits": result["hits"],
                    "diagnostic": result["diagnostic"],
                    "degraded_to": result["degraded_to"],
                }
            else:
                result = store.graph(text, hops=k)
                payload = {"mode": mode, **result}

        payload["count"] = len(payload.get("hits", []))
        payload["request_id"] = request_id
        self._send_json(HTTPStatus.OK, payload, request_id)


def _int_param(query: dict, name: str, default: int, *, minimum: int,
               maximum: int) -> int:
    """Read an integer query parameter, clamped to a documented range."""
    raw = (query.get(name) or [None])[0]
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, value))


def make_server(store_path: str, host: str = "127.0.0.1", port: int = 8099,
                token: str | None = None) -> ApiServer:
    """Build (but do not start) the service.

    Raises ConfigError when the requested bind would expose the store without
    authentication. That check is here, not in `main()`, so a caller that
    embeds the server cannot skip it.
    """
    if not token and not _is_loopback(host):
        raise ConfigError(
            f"refusing to bind {host!r} without MEM20_API_TOKEN: an "
            "unauthenticated memory store must stay on loopback. Set the token "
            "or bind 127.0.0.1.")
    return ApiServer((host, port), store_path=store_path, token=token)


def _check(store_path: str) -> int:
    """One-shot readiness probe. Exit 0 healthy, 1 drifted, 2 unusable."""
    try:
        with open_store(store_path) as store:
            health = store.health()
    except (EngineNotFound, StoreError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(json.dumps(health, indent=2, default=str))
    return 0 if health.get("healthy") else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mem20-api-serve",
        description="HTTP/JSON read surface over a mem20 store.")
    parser.add_argument("--store", default=None,
                        help="store path (default: $MEM20_STORE_PATH, else "
                             "~/.mem20/store)")
    parser.add_argument("--host", default=os.environ.get("MEM20_API_HOST",
                                                         "127.0.0.1"))
    parser.add_argument("--port", type=int,
                        default=int(os.environ.get("MEM20_API_PORT", "8099")))
    parser.add_argument("--check", action="store_true",
                        help="probe the store once and exit; do not serve")
    args = parser.parse_args(argv)

    store_path = (args.store or os.environ.get("MEM20_STORE_PATH")
                  or "~/.mem20/store")
    if args.check:
        return _check(store_path)

    token = os.environ.get("MEM20_API_TOKEN") or None
    try:
        server = make_server(store_path, host=args.host, port=args.port,
                             token=token)
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"error: cannot bind {args.host}:{args.port}: {e}", file=sys.stderr)
        return 2

    host, port = server.server_address[0], server.server_address[1]
    print(json.dumps({
        "service": SERVICE_NAME,
        "api_version": API_VERSION,
        "listening": f"{host}:{port}",
        "store": store_path,
        "auth": "bearer" if token else "none (loopback only)",
    }), flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
