"""mem20facez runtime: CLI + JSON/HTTP + cockpit. Preserves legacy --version/--members."""
from __future__ import annotations
import argparse, json, mimetypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse
from . import __version__, MEMBERS
from .service import FacezService
WEB = Path(__file__).resolve().parent / "web"; SVC = FacezService()

def build_parser():
    p = argparse.ArgumentParser(prog="mem20facez", description="mem20 interface and workspace runtime.")
    p.add_argument("--version", action="store_true"); p.add_argument("--members", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("status"); sub.add_parser("doctor")
    c = sub.add_parser("compose"); c.add_argument("--intent", default="workspace"); c.add_argument("--payload", default="{}")
    s = sub.add_parser("serve"); s.add_argument("--host", default="127.0.0.1"); s.add_argument("--port", type=int, default=8792)
    return p

def _out(obj): print(json.dumps(obj, indent=2, default=str)); return 0

def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.version: print(f"mem20facez {__version__}"); 
    if args.members: 
        for m in MEMBERS: print(m)
    if args.version or args.members: return 0
    cmd = args.cmd or "status"
    if cmd == "status": return _out(SVC.status())
    if cmd == "doctor": return _out(SVC.doctor())
    if cmd == "compose":
        try: payload = json.loads(args.payload)
        except Exception: payload = {"raw": args.payload}
        return _out(SVC.compose(args.intent, payload))
    if cmd == "serve":
        class H(BaseHTTPRequestHandler):
            def _j(self,c,o): b=json.dumps(o,default=str).encode(); self.send_response(c); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
            def _st(self,path):
                rel='index.html' if path in ('/','') else path.lstrip('/'); f=(WEB/rel).resolve()
                try: f.relative_to(WEB.resolve())
                except Exception: return False
                if not f.is_file(): return False
                ct=mimetypes.guess_type(str(f))[0] or 'application/octet-stream';
                if ct.startswith('text/') or ct=='application/javascript': ct+='; charset=utf-8'
                b=f.read_bytes(); self.send_response(200); self.send_header('Content-Type',ct); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b); return True
            def do_GET(self):
                u=urlparse(self.path)
                if u.path in ('/','/index.html','/style.css','/app.js'): return None if self._st(u.path) else self._j(404,{'error':'missing'})
                if u.path=='/health': return self._j(200,{'ok':True,'version':__version__,'members':len(MEMBERS)})
                if u.path=='/status': return self._j(200,SVC.status())
                if u.path=='/doctor': return self._j(200,SVC.doctor())
                if u.path.startswith('/compositions/'):
                    cid = u.path.rsplit('/',1)[-1]
                    return self._j(200,SVC.get_composition(cid))
                return self._j(404,{'error':'not found'})
            def do_POST(self):
                u=urlparse(self.path); n=int(self.headers.get('Content-Length','0') or 0)
                try: body=json.loads(self.rfile.read(n) or b'{}')
                except Exception: body={}
                if u.path=='/compose': return self._j(200,SVC.compose(body.get('intent','workspace'), body.get('payload') or {}, composition_id=body.get('composition_id')))
                if u.path=='/rollback': return self._j(200,SVC.rollback(str(body.get('composition_id') or ''), str(body.get('reason') or 'rollback')))
                if u.path=='/recover': return self._j(200,SVC.recover(str(body.get('composition_id') or '')))
                return self._j(404,{'error':'not found'})
            def log_message(self,*a): pass
        print(f"mem20facez serving on http://{args.host}:{args.port}"); HTTPServer((args.host,args.port),H).serve_forever(); return 0
    return _out(SVC.status())
if __name__ == "__main__": raise SystemExit(main())
