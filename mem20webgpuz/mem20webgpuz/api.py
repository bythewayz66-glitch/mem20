"""mem20webgpuz HTTP API — versioned REST surface with observability endpoints.

Routes
------
``GET  /``                        HTML command surface (browser)
``GET  /health``                  liveness
``GET  /ready``                   readiness (store writable, engine importable)
``GET  /metrics``                 Prometheus text exposition
``GET  /v1/inspect``              runtime + roadmap + config snapshot
``GET  /v1/capabilities``         hardware probe and backend availability
``GET  /v1/jobs``                 recent jobs
``GET  /v1/jobs/<id>``            one job
``POST /v1/jobs/<id>/cancel``     cancel a job
``GET  /v1/events``               event log (``?after=<seq>``)
``GET  /v1/events/stream``        server-sent events (``?seconds=<n>``)
``GET  /v1/resources``            list resources
``GET  /v1/resources/<id>``       one resource
``POST /v1/resources``            create a resource
``POST /v1/resources/<id>``       update (optimistic concurrency)
``DELETE /v1/resources/<id>``     delete
``POST /v1/run``                  execute a job
``POST /v1/feedback``             record a feedback signal
``POST /v1/sync``                 LWW export/merge

Every error response is ``{"error": <Type>, "message": <str>, "details": {...}}``
with a status code derived from the error class, so a client can branch on the
type instead of parsing prose.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from mem20core.mem20core.core import canonical

from .errors import (
    BackendUnavailableError,
    ConfigurationError,
    JobCancelledError,
    JobNotFoundError,
    QuotaExceededError,
    ValidationError,
    WebGPUError,
)
from .runtime import Runtime

__all__ = ["Api", "status_for", "dashboard_html"]

# Error class -> HTTP status. Anything unmapped is a 500.
_STATUS = {
    ValidationError: 400,
    ConfigurationError: 500,
    BackendUnavailableError: 503,
    QuotaExceededError: 429,
    JobCancelledError: 409,
    JobNotFoundError: 404,
}


def status_for(exc: BaseException) -> int:
    """Map an exception to an HTTP status code."""
    for cls in type(exc).__mro__:
        if cls in _STATUS:
            return _STATUS[cls]
    return 500


def dashboard_html(runtime: Runtime) -> str:
    """The browser command surface: run a request, inspect events."""
    roadmap = runtime.roadmap
    rid = int(roadmap.get("global_id", 0))
    title = roadmap.get("title", "")
    outcome = roadmap.get("outcome", "")
    sample = json.dumps({"operations": 1000000, "memory_mb": 256, "cache": False})
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>RM-{rid:03d} {title}</title>
<style>
 body{{font-family:system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 20px;color:#111}}
 h1{{font-size:1.5rem}} .card{{border:1px solid #d0d0d0;border-radius:10px;padding:14px;margin:12px 0}}
 textarea{{width:100%;height:120px;font-family:ui-monospace,monospace;font-size:13px}}
 button{{padding:8px 14px;margin-right:8px;border-radius:8px;border:1px solid #888;background:#f6f6f6;cursor:pointer}}
 pre{{white-space:pre-wrap;background:#111;color:#eee;padding:14px;border-radius:8px;font-size:12px}}
 .muted{{color:#666;font-size:.9rem}}
</style></head><body>
<h1>RM-{rid:03d} &mdash; {title}</h1>
<p>{outcome}</p>
<div class="card"><b>Command surface</b>
<p class="muted">POST a JSON request to <code>/v1/run</code>. The engine reports
<code>speedup: "not_measured"</code> unless a benchmark actually ran.</p>
<textarea id="q">{sample}</textarea><br><br>
<button onclick="run()">Run</button>
<button onclick="events()">Events</button>
<button onclick="caps()">Capabilities</button>
<pre id="o">ready</pre></div>
<script>
async function show(url, opts) {{
  const r = await fetch(url, opts);
  document.getElementById('o').textContent = JSON.stringify(await r.json(), null, 2);
}}
function run() {{
  let body;
  try {{ body = JSON.parse(document.getElementById('q').value); }}
  catch (e) {{ document.getElementById('o').textContent = 'invalid JSON: ' + e.message; return; }}
  show('/v1/run', {{method:'POST', headers:{{'content-type':'application/json'}},
                   body: JSON.stringify({{request: body}})}});
}}
function events() {{ show('/v1/events'); }}
function caps() {{ show('/v1/capabilities'); }}
</script></body></html>"""


class Api:
    """A threaded HTTP server bound to one :class:`Runtime`."""

    def __init__(self, runtime: Runtime) -> None:
        self.runtime = runtime
        self.server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self, host: str | None = None, port: int | None = None) -> tuple[str, int]:
        runtime = self.runtime
        bind_host = host if host is not None else runtime.config.host
        bind_port = port if port is not None else runtime.config.port

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args: Any) -> None:  # noqa: D401 - silence access log
                return

            # -- helpers ---------------------------------------------------
            def _send(self, payload: Any, status: int = 200, ctype: str = "application/json") -> None:
                body = payload if isinstance(payload, (bytes, bytearray)) else canonical(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _body(self) -> dict[str, Any]:
                length = int(self.headers.get("Content-Length", "0") or 0)
                raw = self.rfile.read(length) if length else b"{}"
                if not raw:
                    return {}
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ValidationError("body is not valid JSON", details={"error": str(exc)}) from exc
                if not isinstance(parsed, dict):
                    raise ValidationError("body must be a JSON object")
                return parsed

            def _fail(self, exc: BaseException) -> None:
                if isinstance(exc, WebGPUError):
                    self._send(exc.to_dict(), status_for(exc))
                else:
                    self._send(
                        {"error": type(exc).__name__, "message": str(exc), "details": {}},
                        status=500,
                    )

            # -- GET -------------------------------------------------------
            def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
                parsed = urllib.parse.urlparse(self.path)
                query = urllib.parse.parse_qs(parsed.query)
                path = parsed.path
                try:
                    if path == "/health":
                        return self._send(runtime.health())
                    if path == "/ready":
                        payload = runtime.readiness()
                        return self._send(payload, 200 if payload["ready"] else 503)
                    if path == "/metrics":
                        return self._send(
                            runtime.metrics.prometheus().encode(), ctype="text/plain; charset=utf-8"
                        )
                    if path == "/v1/inspect":
                        return self._send(runtime.inspect())
                    if path == "/v1/capabilities":
                        from . import webgpu

                        probe = webgpu.probe_hardware()
                        chosen, alternatives = webgpu.select_backend({}, probe)
                        return self._send(
                            {
                                "probe": probe.to_dict(),
                                "chosen": chosen.to_dict(),
                                "alternatives": [b.to_dict() for b in alternatives],
                            }
                        )
                    if path == "/v1/jobs":
                        return self._send(runtime.store.list_jobs(int(query.get("limit", ["100"])[0])))
                    if path.startswith("/v1/jobs/"):
                        jid = path.split("/")[3]
                        return self._send(runtime.store.require_job(jid))
                    if path == "/v1/events":
                        return self._send(runtime.store.events(int(query.get("after", ["0"])[0])))
                    if path == "/v1/events/stream":
                        return self._stream(
                            int(query.get("after", ["0"])[0]),
                            min(30.0, float(query.get("seconds", ["5"])[0])),
                        )
                    if path == "/v1/resources":
                        return self._send(runtime.store.resource_list(int(query.get("limit", ["100"])[0])))
                    if path.startswith("/v1/resources/"):
                        rid = path.split("/")[3]
                        found = runtime.store.resource_get(rid)
                        if found is None:
                            raise JobNotFoundError("no such resource", details={"id": rid})
                        return self._send(found)
                    if path == "/":
                        return self._send(
                            dashboard_html(runtime).encode(), ctype="text/html; charset=utf-8"
                        )
                    return self._send({"error": "NotFound", "message": "no such route"}, 404)
                except Exception as exc:  # noqa: BLE001 - mapped to a status
                    return self._fail(exc)

            def _stream(self, after: int, seconds: float) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "close")
                self.end_headers()
                deadline = time.time() + seconds
                while time.time() < deadline:
                    rows = runtime.store.events(after, 100)
                    for row in rows:
                        after = max(after, int(row["seq"]))
                        frame = f"event: {row['kind']}\ndata: {canonical(row)}\n\n"
                        self.wfile.write(frame.encode())
                    self.wfile.flush()
                    time.sleep(0.1)

            # -- POST ------------------------------------------------------
            def do_POST(self) -> None:  # noqa: N802
                path = urllib.parse.urlparse(self.path).path
                try:
                    body = self._body()
                    if path == "/v1/run":
                        request = body.get("request", body)
                        result = runtime.run(request, body.get("idempotency_key"))
                        return self._send(result.to_dict())
                    if path == "/v1/feedback":
                        runtime.store.feedback(
                            str(body["signal"]), float(body["value"]), str(body.get("note", ""))
                        )
                        return self._send({"ok": True})
                    if path == "/v1/resources":
                        return self._send(
                            runtime.store.resource_create(body.get("body", body), body.get("id")), 201
                        )
                    if path.startswith("/v1/resources/"):
                        rid = path.split("/")[3]
                        return self._send(
                            runtime.store.resource_update(
                                rid, body.get("body", body), body.get("expected_version")
                            )
                        )
                    if path == "/v1/sync":
                        merged = runtime.store.merge_lww(body.get("rows", []))
                        return self._send({"merged": merged, "rows": runtime.store.export_lww()})
                    if path.startswith("/v1/jobs/") and path.endswith("/cancel"):
                        jid = path.split("/")[3]
                        return self._send({"cancelled": runtime.cancel(jid)})
                    return self._send({"error": "NotFound", "message": "no such route"}, 404)
                except Exception as exc:  # noqa: BLE001
                    return self._fail(exc)

            # -- DELETE ----------------------------------------------------
            def do_DELETE(self) -> None:  # noqa: N802
                path = urllib.parse.urlparse(self.path).path
                try:
                    if path.startswith("/v1/resources/"):
                        rid = path.split("/")[3]
                        return self._send({"deleted": runtime.store.resource_delete(rid)})
                    return self._send({"error": "NotFound", "message": "no such route"}, 404)
                except Exception as exc:  # noqa: BLE001
                    return self._fail(exc)

        self.server = ThreadingHTTPServer((bind_host, int(bind_port)), Handler)
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()
        host_out, port_out = self.server.server_address[:2]
        return str(host_out), int(port_out)

    def stop(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
