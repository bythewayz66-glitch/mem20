"""CLI + JSON HTTP API + cockpit for mem20enginez crew runtime."""
from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import __version__
from .domain import MEMBERS
from .service import ConflictError, EngineRuntimeService, NotFoundError, ValidationError

WEB_DIR = Path(__file__).with_name("web")


def _j(o): return json.dumps(o, indent=2, sort_keys=True, default=str)


def _read_json(text):
    if not text: return {}
    t = text.strip()
    if t.startswith("@"): return json.loads(Path(t[1:]).read_text())
    return json.loads(t)


class Handler(BaseHTTPRequestHandler):
    svc: EngineRuntimeService = None  # type: ignore

    def _send(self, code, obj, ctype="application/json; charset=utf-8"):
        body = obj if isinstance(obj, (bytes, bytearray)) else _j(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _err(self, code, e): self._send(code, {"ok": False, "error": type(e).__name__, "message": str(e)})

    def _body(self):
        n = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        return json.loads(raw) if raw else {}

    def _static(self, path):
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        f = (WEB_DIR / rel).resolve()
        try:
            f.relative_to(WEB_DIR.resolve())
        except Exception:
            return False
        if not f.is_file():
            return False
        ctype = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype == "application/javascript":
            ctype += "; charset=utf-8"
        self._send(200, f.read_bytes(), ctype)
        return True

    def do_OPTIONS(self): self._send(204, b"")

    def do_GET(self):
        try:
            u = urlparse(self.path); p = u.path.rstrip("/") or "/"; q = parse_qs(u.query)
            if p == "/":
                if not self._static("/"): self._err(404, FileNotFoundError("index.html"))
                return
            if self._static(p): return
            if p in ("/health", "/api/health"): return self._send(200, {"ok": True, "service": "mem20enginez", "version": __version__})
            if p in ("/status", "/api/status"): return self._send(200, self.svc.status())
            if p == "/api/doctor": return self._send(200, self.svc.doctor())
            if p in ("/api/members", "/members"): return self._send(200, self.svc.members())
            if p == "/api/plans": return self._send(200, {"ok": True, "plans": self.svc.plans(int(q.get("limit", ["50"])[0]))})
            if p.startswith("/api/plans/"): return self._send(200, {"ok": True, "plan": self.svc.get_plan(p.rsplit("/", 1)[1])})
            if p == "/api/runs": return self._send(200, {"ok": True, "runs": self.svc.runs(int(q.get("limit", ["100"])[0]))})
            if p == "/api/events": return self._send(200, {"ok": True, "events": self.svc.events(int(q.get("since", ["0"])[0]), int(q.get("limit", ["200"])[0]))})
            return self._err(404, KeyError(p))
        except NotFoundError as e: self._err(404, e)
        except Exception as e: self._err(500, e)

    def do_POST(self):
        try:
            p = urlparse(self.path).path.rstrip("/")
            b = self._body() if int(self.headers.get("Content-Length", "0") or 0) else {}
            if p in ("/api/plan", "/plan"): return self._send(200, self.svc.plan(str(b.get("intent") or ""), b))
            if p in ("/api/execute", "/execute"): return self._send(200, self.svc.execute(b))
            if p == "/api/snapshot": return self._send(200, self.svc.snapshot(str(b.get("label") or "")))
            if p == "/api/restore": return self._send(200, self.svc.restore(str(b.get("snapshot_id") or "")))
            if p == "/api/simulate": return self._send(200, self.svc.simulate())
            if p == "/api/benchmark": return self._send(200, self.svc.benchmark(int(b.get("iterations") or 20)))
            return self._err(404, KeyError(p))
        except NotFoundError as e: self._err(404, e)
        except ConflictError as e: self._err(409, e)
        except (ValidationError, ValueError, KeyError) as e: self._err(400, e)
        except Exception as e: self._err(500, e)

    def log_message(self, *a): return


def serve(svc, host="127.0.0.1", port=8785):
    class H(Handler): pass
    H.svc = svc
    return ThreadingHTTPServer((host, port), H)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mem20enginez", description="mem20 crew runtime for engine members")
    ap.add_argument("--db", default="state/mem20enginez.sqlite3")
    ap.add_argument("--estate-root", default=None)
    ap.add_argument("--version", action="store_true", help="Print version and exit")
    ap.add_argument("--members", action="store_true", help="List the registered engine members")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("status")
    sub.add_parser("doctor")
    sub.add_parser("members")
    sub.add_parser("simulate")
    b = sub.add_parser("benchmark"); b.add_argument("--iterations", type=int, default=20)
    p = sub.add_parser("plan"); p.add_argument("--intent", required=True); p.add_argument("--json")
    ev = sub.add_parser("events"); ev.add_argument("--since", type=int, default=0); ev.add_argument("--limit", type=int, default=50)
    sv = sub.add_parser("serve"); sv.add_argument("--host", default="127.0.0.1"); sv.add_argument("--port", type=int, default=8785)
    ex = sub.add_parser("execute"); ex.add_argument("json", nargs="?", default="{}")
    args = ap.parse_args(argv)
    if args.version:
        print(f"{ap.prog} {__version__}")
        return 0
    if args.members:
        for name in MEMBERS:
            print(name)
        return 0
    if not args.cmd:
        ap.print_help()
        return 0
    svc = EngineRuntimeService(args.db, estate_root=args.estate_root)
    try:
        if args.cmd == "status": print(_j(svc.status()))
        elif args.cmd == "doctor": print(_j(svc.doctor()))
        elif args.cmd == "members": print(_j(svc.members()))
        elif args.cmd == "simulate": print(_j(svc.simulate()))
        elif args.cmd == "benchmark": print(_j(svc.benchmark(args.iterations)))
        elif args.cmd == "plan": print(_j(svc.plan(args.intent, _read_json(args.json) if args.json else {})))
        elif args.cmd == "events": print(_j({"ok": True, "events": svc.events(args.since, args.limit)}))
        elif args.cmd == "serve":
            h = serve(svc, args.host, args.port)
            print(f"serving mem20enginez on http://{args.host}:{h.server_address[1]}", flush=True)
            h.serve_forever()
        elif args.cmd == "execute": print(_j(svc.execute(_read_json(args.json))))
        else: ap.print_help(); return 2
        return 0
    except (NotFoundError, ConflictError, ValidationError, ValueError) as e:
        print(_j({"ok": False, "error": type(e).__name__, "message": str(e)}))
        return 1
