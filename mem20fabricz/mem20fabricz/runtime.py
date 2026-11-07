"""mem20fabricz runtime: CLI + JSON/HTTP API + static cockpit. Preserves legacy --version/--members."""
from __future__ import annotations
import argparse, json, mimetypes, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse
from . import __version__, MEMBERS
from .service import FabricService

WEB = Path(__file__).resolve().parent / "web"
SVC = FabricService()

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mem20fabricz", description="mem20 integration fabric runtime.")
    # legacy flags (compat)
    p.add_argument("--version", action="store_true", help="Print the version and exit.")
    p.add_argument("--members", action="store_true", help="List member systems and exit.")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("status", help="Member registry/import status")
    sub.add_parser("doctor", help="Member + 6-peer health probe")
    d = sub.add_parser("dispatch", help="Plan/dispatch an integration intent")
    d.add_argument("--intent", default="integrate")
    d.add_argument("--payload", default="{}")
    s = sub.add_parser("serve", help="HTTP API + cockpit")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8791)
    sub.add_parser("probe", help="Probe members and peers")
    return p

def _out(obj):
    print(json.dumps(obj, indent=2, default=str)); return 0

def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    # legacy compat behavior
    if args.version:
        print(f"mem20fabricz {__version__}")
        if not args.cmd and not args.members: return 0
    if args.members:
        for m in MEMBERS: print(m)
        if not args.cmd and not args.version: return 0
    if args.version or args.members: return 0
    cmd = args.cmd or "status"
    if cmd == "status": return _out(SVC.status())
    if cmd == "doctor": return _out(SVC.doctor())
    if cmd == "probe": return _out(SVC.probe(include_signals=True))
    if cmd == "dispatch":
        try: payload = json.loads(args.payload)
        except Exception: payload = {"raw": args.payload}
        return _out(SVC.dispatch(args.intent, payload))
    if cmd == "serve":
        serve(args.host, args.port); return 0
    return _out(SVC.status())

def serve(host, port):
    svc = SVC
    class H(BaseHTTPRequestHandler):
        def _json(self, code, obj):
            b = json.dumps(obj, default=str).encode(); self.send_response(code)
            self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
        def _static(self, path):
            rel = 'index.html' if path in ('/','') else path.lstrip('/')
            f = (WEB/rel).resolve()
            try: f.relative_to(WEB.resolve())
            except Exception: return False
            if not f.is_file(): return False
            ct = mimetypes.guess_type(str(f))[0] or 'application/octet-stream'
            if ct.startswith('text/') or ct=='application/javascript': ct += '; charset=utf-8'
            b = f.read_bytes(); self.send_response(200); self.send_header('Content-Type',ct); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return True
        def do_GET(self):
            u = urlparse(self.path)
            if u.path in ('/','/index.html','/style.css','/app.js'): return None if self._static(u.path) else self._json(404,{'error':'missing'})
            if u.path == '/health': return self._json(200, {'ok': True, 'version': __version__, 'members': len(MEMBERS)})
            if u.path == '/status': return self._json(200, svc.status())
            if u.path == '/doctor': return self._json(200, svc.doctor())
            return self._json(404, {'error': 'not found'})
        def do_POST(self):
            u = urlparse(self.path); n = int(self.headers.get('Content-Length','0') or 0)
            try: body = json.loads(self.rfile.read(n) or b'{}')
            except Exception: body = {}
            if u.path == '/dispatch': return self._json(200, svc.dispatch(body.get('intent','integrate'), body.get('payload') or {}))
            return self._json(404, {'error': 'not found'})
        def log_message(self, *a): pass
    print(f"mem20fabricz serving on http://{host}:{port}")
    HTTPServer((host, port), H).serve_forever()

if __name__ == "__main__":
    raise SystemExit(main())
