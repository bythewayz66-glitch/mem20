"""CLI + JSON HTTP + cockpit for episodic memory graph."""
from __future__ import annotations
import argparse, json, mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
__version__ = "1.0.0"
from .service import ConflictError, EpisodicService, NotFoundError, ValidationError

WEB_DIR = Path(__file__).with_name("web")
def _j(o): return json.dumps(o, indent=2, sort_keys=True, default=str)
def _rj(t):
    if not t: return {}
    t=t.strip(); return json.loads(Path(t[1:]).read_text()) if t.startswith("@") else json.loads(t)

class H(BaseHTTPRequestHandler):
    svc: EpisodicService = None  # type: ignore
    def _send(self, code, obj, ctype="application/json; charset=utf-8"):
        b = obj if isinstance(obj,(bytes,bytearray)) else _j(obj).encode()
        self.send_response(code); self.send_header("Content-Type",ctype); self.send_header("Content-Length",str(len(b)))
        self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Content-Type"); self.send_header("Access-Control-Allow-Methods","GET,POST,DELETE,OPTIONS")
        self.end_headers(); self.wfile.write(b)
    def _err(self,code,e): self._send(code,{"ok":False,"error":type(e).__name__,"message":str(e)})
    def _body(self): n=int(self.headers.get("Content-Length","0") or 0); r=self.rfile.read(n) if n else b"{}"; return json.loads(r) if r else {}
    def _static(self,p):
        rel="index.html" if p in ("/","") else p.lstrip("/"); f=(WEB_DIR/rel).resolve()
        try: f.relative_to(WEB_DIR.resolve())
        except Exception: return False
        if not f.is_file(): return False
        ct=mimetypes.guess_type(str(f))[0] or "application/octet-stream"
        if ct.startswith("text/") or ct=="application/javascript": ct+="; charset=utf-8"
        self._send(200,f.read_bytes(),ct); return True
    def do_OPTIONS(self): self._send(204,b"")
    def do_GET(self):
        try:
            u=urlparse(self.path); p=u.path.rstrip("/") or "/"; q=parse_qs(u.query)
            if p=="/":
                if not self._static("/"): self._err(404,FileNotFoundError("index.html")); return
            if self._static(p): return
            if p in ("/health","/api/health"): return self._send(200,{"ok":True,"service":"mem20episodicmemorygraphz"})
            if p in ("/status","/api/status"): return self._send(200,self.svc.status())
            if p=="/api/doctor": return self._send(200,self.svc.doctor())
            if p=="/api/episodes": return self._send(200,self.svc.list(int(q.get("limit",["200"])[0])))
            if p=="/api/graph": return self._send(200,self.svc.graph())
            if p=="/api/timeline": return self._send(200,self.svc.timeline(int(q.get("limit",["100"])[0])))
            if p=="/api/events": return self._send(200,{"ok":True,"events":self.svc.events(int(q.get("since",["0"])[0]),int(q.get("limit",["200"])[0]))})
            if p.startswith("/api/episodes/") and p.endswith("/neighbors"): return self._send(200,self.svc.neighbors(p.split("/")[3]))
            if p.startswith("/api/episodes/"): return self._send(200,self.svc.get(p.rsplit("/",1)[1]))
            return self._err(404,KeyError(p))
        except NotFoundError as e: self._err(404,e)
        except Exception as e: self._err(500,e)
    def do_POST(self):
        try:
            p=urlparse(self.path).path.rstrip("/"); b=self._body() if int(self.headers.get("Content-Length","0") or 0) else {}
            if p=="/api/episodes": return self._send(200,self.svc.create_episode(str(b.get("title") or ""), b.get("events"), b.get("entities"), b.get("metadata"), episode_id=b.get("episode_id") or b.get("id"), idempotency_key=b.get("idempotency_key")))
            if p=="/api/events/add" or p=="/api/episode/event": return self._send(200,self.svc.add_event(str(b.get("episode_id") or b.get("id") or ""), dict(b.get("event") or b), expected_version=b.get("expected_version")))
            if p=="/api/link": return self._send(200,self.svc.link(str(b.get("src") or ""), str(b.get("dst") or ""), str(b.get("relation") or "follows")))
            if p in ("/api/recall","/recall"): return self._send(200,self.svc.recall(str(b.get("query") or b.get("q") or ""), int(b.get("limit") or 50), since=b.get("since"), until=b.get("until"), entity=b.get("entity"), expand_graph=bool(b.get("expand_graph"))))
            if p in ("/api/query","/query"): return self._send(200,self.svc.query(b))
            if p=="/api/forget": return self._send(200,self.svc.forget(float(b.get("older_than") or b.get("seconds") or 0)))
            if p=="/api/snapshot": return self._send(200,self.svc.snapshot(str(b.get("label") or "")))
            if p=="/api/restore": return self._send(200,self.svc.restore(str(b.get("snapshot_id") or "")))
            if p=="/api/simulate": return self._send(200,self.svc.simulate())
            if p=="/api/benchmark": return self._send(200,self.svc.benchmark(int(b.get("iterations") or 20)))
            if p=="/execute": return self._send(200,self.svc.execute(b))
            return self._err(404,KeyError(p))
        except NotFoundError as e: self._err(404,e)
        except ConflictError as e: self._err(409,e)
        except (ValidationError,ValueError,KeyError) as e: self._err(400,e)
        except Exception as e: self._err(500,e)
    def log_message(self,*a): return

def serve(svc,host="127.0.0.1",port=8786):
    class S(H): pass
    S.svc=svc; return ThreadingHTTPServer((host,port),S)

def main(argv=None):
    ap=argparse.ArgumentParser(prog="mem20episodicmemorygraphz", description="Episodic Memory Graph (RM-021)")
    ap.add_argument("--db", default="state/mem20episodicmemorygraphz.sqlite3")
    ap.add_argument("--version", action="store_true")
    sub=ap.add_subparsers(dest="cmd")
    sub.add_parser("status"); sub.add_parser("doctor"); sub.add_parser("simulate"); sub.add_parser("graph"); sub.add_parser("timeline")
    b=sub.add_parser("benchmark"); b.add_argument("--iterations", type=int, default=20)
    c=sub.add_parser("create"); c.add_argument("--title", required=True)
    e=sub.add_parser("event"); e.add_argument("--episode", required=True); e.add_argument("--json", required=True)
    l=sub.add_parser("link"); l.add_argument("--src", required=True); l.add_argument("--dst", required=True); l.add_argument("--relation", default="follows")
    r=sub.add_parser("recall"); r.add_argument("query"); r.add_argument("--limit", type=int, default=20)
    q=sub.add_parser("query"); q.add_argument("--json")
    sv=sub.add_parser("serve"); sv.add_argument("--host", default="127.0.0.1"); sv.add_argument("--port", type=int, default=8786)
    ex=sub.add_parser("execute"); ex.add_argument("json", nargs="?", default="{}")
    a=ap.parse_args(argv)
    if a.version: print(f"{ap.prog} {__version__}"); return 0
    if not a.cmd: ap.print_help(); return 0
    svc=EpisodicService(a.db)
    try:
        if a.cmd=="status": print(_j(svc.status()))
        elif a.cmd=="doctor": print(_j(svc.doctor()))
        elif a.cmd=="simulate": print(_j(svc.simulate()))
        elif a.cmd=="benchmark": print(_j(svc.benchmark(a.iterations)))
        elif a.cmd=="graph": print(_j(svc.graph()))
        elif a.cmd=="timeline": print(_j(svc.timeline()))
        elif a.cmd=="create": print(_j(svc.create_episode(a.title)))
        elif a.cmd=="event": print(_j(svc.add_event(a.episode, _rj(a.json))))
        elif a.cmd=="link": print(_j(svc.link(a.src,a.dst,a.relation)))
        elif a.cmd=="recall": print(_j(svc.recall(a.query,a.limit)))
        elif a.cmd=="query": print(_j(svc.query(_rj(a.json) if a.json else {})))
        elif a.cmd=="serve":
            h=serve(svc,a.host,a.port); print(f"serving mem20episodicmemorygraphz on http://{a.host}:{h.server_address[1]}", flush=True); h.serve_forever()
        elif a.cmd=="execute": print(_j(svc.execute(_rj(a.json))))
        else: ap.print_help(); return 2
        return 0
    except (NotFoundError,ConflictError,ValidationError,ValueError) as e:
        print(_j({"ok":False,"error":type(e).__name__,"message":str(e)})); return 1
