"""mem20labz HTTP/JSON API and served web frontend."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse, parse_qs

from .runtime import LabRuntime

INDEX_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>mem20labz — Laboratory Runtime</title>
<style>body{font:15px/1.5 system-ui,sans-serif;max-width:1100px;margin:1.5rem auto;padding:0 1rem;background:#0b1020;color:#e8eefc}
h1,h2{margin:.2rem 0} .card{background:#141c33;border:1px solid #26345f;border-radius:10px;padding:1rem;margin:.75rem 0}
pre{background:#080c18;padding:.75rem;border-radius:8px;overflow:auto} button{background:#3b82f6;color:#fff;border:0;padding:.45rem .8rem;border-radius:7px;cursor:pointer;margin-right:.4rem}
a{color:#93c5fd} .muted{color:#9fb0d0} .ok{color:#86efac} .bad{color:#fca5a5}</style></head>
<body>
<h1>mem20labz</h1><p class="muted">Laboratory runtime control plane for 10 member labs (registry, probes, simulations, 6-peer ecosystem signals, durable run history).</p>
<div class="card"><button onclick="load('/api/status')">Status</button><button onclick="load('/api/registry')">Registry</button><button onclick="load('/api/probe')">Probe all</button><button onclick="load('/api/signals')">Ecosystem signals</button><button onclick="load('/api/simulate')">Simulate all</button><button onclick="load('/api/history?limit=20')">History</button></div>
<div class="card"><h2>Response</h2><pre id="out">Loading status…</pre></div>
<script>
async function load(p){const r=await fetch(p); const j=await r.json(); document.getElementById('out').textContent=JSON.stringify(j,null,2);}
load('/api/status');
</script></body></html>"""


def make_handler(runtime: LabRuntime):
    class Handler(BaseHTTPRequestHandler):
        def _json(self, code: int, obj: Any):
            body = json.dumps(obj, indent=2, default=str).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _html(self, code: int, html: str):
            body = html.encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            u = urlparse(self.path)
            qs = parse_qs(u.query)
            try:
                if u.path in ("/", "/index.html"):
                    return self._html(200, INDEX_HTML)
                if u.path == "/api/status":
                    return self._json(200, runtime.status())
                if u.path == "/api/registry":
                    return self._json(200, runtime.registry())
                if u.path == "/api/probe":
                    member = (qs.get("member") or [None])[0]
                    return self._json(200, runtime.probe(member))
                if u.path == "/api/simulate":
                    member = (qs.get("member") or [None])[0]
                    return self._json(200, runtime.simulate(member))
                if u.path == "/api/signals":
                    return self._json(200, runtime.signals())
                if u.path == "/api/history":
                    limit = int((qs.get("limit") or ["50"])[0])
                    return self._json(200, runtime.history(limit))
                if u.path == "/health":
                    return self._json(200, {"ok": True, "service": "mem20labz"})
                return self._json(404, {"ok": False, "error": "not_found", "path": u.path})
            except Exception as e:
                return self._json(500, {"ok": False, "error": f"{type(e).__name__}: {e}"})

        def log_message(self, format, *args):
            return

    return Handler


def serve(host: str = "127.0.0.1", port: int = 8841, db_path: str | None = None) -> ThreadingHTTPServer:
    runtime = LabRuntime(db_path=db_path)
    httpd = ThreadingHTTPServer((host, port), make_handler(runtime))
    return httpd
