# mem20 HTTP API service — 4.0 server lane

**Lane:** server / backend · **Date:** 2026-11-01 · **Base:** `main` @ `48c241a1edff1fdc9f0d0b38f51796c3c8b88b2b` (`VERSION` 3.1.2)

## 1. The gap this closes

Before this change the tree had exactly one HTTP surface, `bridge/server.py`, and it
imports `fastapi`, `uvicorn` and `httpx` at module scope:

```
$ head -40 bridge/server.py | grep -nE '^(from|import) (fastapi|httpx)'
35:from fastapi import FastAPI, HTTPException, Query
36:from fastapi.middleware.cors import CORSMiddleware
37:from fastapi.responses import JSONResponse
38:import httpx
```

None of those are installed on a stock host, so the service cannot start from a clean
checkout. Worse, the failure mode is an `ImportError` at import time — a supervisor sees a
process that exits immediately and cannot distinguish it from a crash loop, and there is no
liveness endpoint to ask.

`mem20api` (the supported Python API over the engine) had no network surface at all. The
4.0 server lane needs one that starts with zero third-party packages.

## 2. What landed

| File | Purpose |
|---|---|
| `mem20api/mem20api/http_server.py` | The service. Standard library only (`http.server`, `json`, `hmac`, `threading`). |
| `mem20api/tests/test_http_server.py` | 22 tests against a real socket and a real temporary store. |
| `systemd/mem20-api.service.template` | Hardened unit; token from `EnvironmentFile`, `ExecStartPre` readiness gate. |
| `.github/workflows/ci.yml` | New `mem20api-http` job running the suite. |

### Design decisions, and why

**Standard library only.** `http.server.ThreadingHTTPServer` is enough for a read surface
that answers a handful of JSON routes. A `git clone --depth 1` checkout serves requests with
no `pip install`, which is the property the FastAPI bridge lacks.

**Fail-closed binding.** `make_server()` raises `ConfigError` when asked to bind a
non-loopback address with no `MEM20_API_TOKEN`. The check lives in `make_server`, not in
`main()`, so an embedder cannot skip it. An unauthenticated memory store stays on loopback.

**Honest status codes.** `/readyz` returns **503** when the store's indexes have drifted,
not `200` with `healthy: false` in the body — a load balancer reads the status line, not the
JSON. `/healthz` never touches the store, so a supervisor can tell "starting" from "dead".

**One store, one lock.** The engine resolves its paths as module globals and `_rebind()`
reassigns them on every call. Two threads inside one store would rebind each other's paths
and a write would land in the wrong store — silent, and exactly the bug `mem20api` exists to
prevent. The HTTP layer is threaded; every store call is serialised through
`server.store_lock`.

**Bounded input.** Bodies over 64 KiB are refused with 413 rather than buffered. `k` and
`limit` are clamped to documented ranges. Every error is JSON with a stable `code`, and
every response carries a 16-hex `X-Request-Id` so a log line can be matched to a request.

## 3. Endpoints

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/healthz` | public | liveness; never opens the store |
| GET | `/readyz` | bearer | 200 healthy / **503 drifted** |
| GET | `/v1/stats` | bearer | counts; `health` blob stripped |
| GET | `/v1/ledger?k=20` | bearer | `k` clamped 1..500 |
| GET | `/v1/entities?limit=50` | bearer | `limit` clamped 1..500 |
| POST | `/v1/recall` | bearer | `{topic?, tags?, k?}` |
| POST | `/v1/query` | bearer | `{query, mode: semantic\|hybrid\|graph, k}` |

## 4. Verification — real output

### 4.1 Test suite

```
$ PYTHONPATH=mem20api python3 -m pytest -q mem20api/tests
......................                                                   [100%]
22 passed, 1 warning in 9.59s
```

The 22 tests cover: the non-loopback-without-token refusal, loopback-without-token
acceptance, `/healthz` answering with no token, `/readyz` rejecting a missing and a wrong
token, a write-then-read round trip through HTTP, hybrid query reporting `degraded_to`,
empty/unknown-mode/non-integer-`k`/non-string-tags validation, invalid JSON as 400 (not
500), oversized body as 413, JSON 404, 405 with an `Allow` header, and the request id on
every response.

### 4.2 Live process, real socket

```
$ MEM20_API_TOKEN=<redacted> PYTHONPATH=mem20api \
    python3 -m mem20api.http_server --store /tmp/m20live --port 8099
{"service": "mem20-api", "api_version": "1", "listening": "127.0.0.1:8099",
 "store": "/tmp/m20live", "auth": "bearer"}
```

Liveness, no token:

```
$ curl -s -w "HTTP %{http_code}\n" http://127.0.0.1:8099/healthz
HTTP 200
{"status": "ok", "service": "mem20-api", "api_version": "1", "uptime_s": 3.963,
 "request_id": "498de1e714ff43c6"}
```

Readiness, no token — refused:

```
$ curl -s -w "HTTP %{http_code}\n" http://127.0.0.1:8099/readyz
HTTP 401
{"error": {"code": "unauthorised", "message": "a valid bearer token is required"},
 "request_id": "bfb547d878d247d9"}
```

Readiness, with token — an empty store is honestly **not** ready:

```
$ curl -s -w "HTTP %{http_code}\n" -H "Authorization: Bearer <redacted>" \
    http://127.0.0.1:8099/readyz
HTTP 503
{"status": "drifted", "store": "/tmp/m20live", "ledger_records": 0,
 "indexes": {"vector": {"index": "vector", "present": false, "healthy": false},
             "bm25":   {"index": "bm25",   "present": false, "healthy": false},
             "graph":  {"index": "graph",  "present": false, "healthy": false}},
 "request_id": "b6f02d9b9ecb4341"}
```

Stats:

```
$ curl -s -w "\nHTTP %{http_code}\n" -H "Authorization: Bearer <redacted>" \
    http://127.0.0.1:8099/v1/stats
{"path": "/tmp/m20live", "ledger_events": 0, "grounded_facts": 0, "topics": 0,
 "vector_available": false, "bm25_available": false, "request_id": "f3b6057d37864696"}
HTTP 200
```

Hybrid query with no retrieval deps installed — the degradation is reported, not hidden:

```
$ curl -s -w "\nHTTP %{http_code}\n" -X POST -H "Authorization: Bearer <redacted>" \
    -H 'Content-Type: application/json' \
    -d '{"query":"prod build","mode":"hybrid","k":3}' \
    http://127.0.0.1:8099/v1/query
{"mode": "hybrid", "hits": [{"error": "No search dependencies installed"}],
 "diagnostic": {}, "degraded_to": "unknown", "count": 1,
 "request_id": "7150a6a250ad43d8"}
HTTP 200
```

Unknown route:

```
$ curl -s -w "\nHTTP %{http_code}\n" -H "Authorization: Bearer <redacted>" \
    http://127.0.0.1:8099/v1/nope
{"error": {"code": "not_found", "message": "no route for /v1/nope"},
 "request_id": "364f695a3591472c"}
HTTP 404
```

## 5. Deploying it

```bash
# 1. token, mode 0600, outside the tree
sudo install -d -m 0750 /etc/mem20
sudo install -m 0600 /dev/null /etc/mem20/api.env
printf 'MEM20_API_TOKEN=%s\n' "$(openssl rand -hex 32)" | sudo tee /etc/mem20/api.env >/dev/null

# 2. render the unit
sed -e "s|__MEM20_USER__|mem20|g" \
    -e "s|__MEM20_WORKDIR__|/opt/mem20/mem20|g" \
    -e "s|__MEM20_STORE_PATH__|/var/lib/mem20/store|g" \
    -e "s|__MEM20_VENV_PYTHON__|/opt/mem20/venv/bin/python|g" \
    systemd/mem20-api.service.template | sudo tee /etc/systemd/system/mem20-api.service >/dev/null

# 3. start
sudo systemctl daemon-reload
sudo systemctl enable --now mem20-api
systemctl status mem20-api --no-pager
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8099/healthz   # expect 200
```

The unit binds `127.0.0.1` only. To expose it, put a TLS-terminating reverse proxy in front
and keep the bearer token — do not change `MEM20_API_HOST` to `0.0.0.0` and leave the token
unset, because `make_server` will refuse to start (by design).

## 6. What this does not do

- **No write endpoints.** `remember`, `supersede` and `promote` are deliberately absent from
  the HTTP surface. A network write path into a memory store needs an auth model richer than
  one shared bearer token; that is a separate decision, not an oversight.
- **No TLS.** Terminate at a proxy.
- **No rate limiting.** One token, loopback bind; a proxy is the right place for it.
- **`degraded_to: "unknown"`** on a store with no retrieval deps is the engine's own
  diagnostic value, passed through unchanged rather than invented.
