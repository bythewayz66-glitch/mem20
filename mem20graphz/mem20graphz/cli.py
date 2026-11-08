"""Crew runtime CLI for mem20graphz (#321). Preserves --version/--members."""
from __future__ import annotations
import argparse, json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional, Sequence
from urllib.parse import urlparse
import mimetypes

from . import MEMBERS, __version__, domain, ecosystem

WEB_DIR = Path(__file__).with_name("web")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mem20graphz", description="mem20 graph systems runtime.")
    parser.add_argument("--version", action="store_true", help="Print the version and exit.")
    parser.add_argument("--members", action="store_true", help="List member systems and exit.")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("doctor")
    sub.add_parser("status")
    s = sub.add_parser("serve"); s.add_argument("--host", default="127.0.0.1"); s.add_argument("--port", type=int, default=0)
    return parser

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body if isinstance(body, (bytes, bytearray)) else json.dumps(body, indent=2).encode()
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b))); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            f = WEB_DIR / "index.html"
            if f.is_file(): return self._send(200, f.read_bytes(), "text/html; charset=utf-8")
            return self._send(200, {"crew": "mem20graphz", "members": list(MEMBERS)})
        if u.path in ("/style.css", "/app.js"):
            f = WEB_DIR / u.path.lstrip("/")
            if f.is_file():
                ct = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
                if ct.startswith("text/") or ct == "application/javascript": ct += "; charset=utf-8"
                return self._send(200, f.read_bytes(), ct)
        if u.path in ("/doctor", "/api/doctor", "/health"):
            return self._send(200, ecosystem.probe())
        if u.path == "/status":
            return self._send(200, domain.crew_summary())
        self._send(404, {"error": "not found"})
    def log_message(self, *a): pass

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(f"mem20graphz {__version__}")
    if args.members:
        for member in MEMBERS:
            print(member)
    if args.version or args.members:
        return 0
    if args.cmd == "doctor":
        print(json.dumps(ecosystem.probe(), indent=2)); return 0
    if args.cmd == "status":
        print(json.dumps(domain.crew_summary(), indent=2)); return 0
    if args.cmd == "serve":
        srv = ThreadingHTTPServer((args.host, args.port), Handler)
        print(f"http://{args.host}:{srv.server_port}", flush=True); srv.serve_forever()
    return 0

if __name__ == "__main__":
    sys.exit(main())
