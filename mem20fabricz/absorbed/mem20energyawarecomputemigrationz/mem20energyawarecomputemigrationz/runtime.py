"""CLI + JSON HTTP API + static cockpit for energy-aware compute migration."""

from __future__ import annotations
import argparse, json, mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from .service import ConflictError, MigrationService, NotFoundError, ValidationError

WEB_DIR = Path(__file__).with_name("web")
def _j(o): return json.dumps(o, indent=2, sort_keys=True, default=str)
def _read_json(t):
    if not t: return {}
    t=t.strip()
    if t.startswith("@"): return json.loads(Path(t[1:]).read_text())
    return json.loads(t)

class Handler(BaseHTTPRequestHandler):
    svc: MigrationService = None  # type: ignore
    def _send(self, code, obj, ctype="application/json; charset=utf-8"):
        body = obj if isinstance(obj,(bytes,bytearray)) else _j(obj).encode()
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Content-Type"); self.send_header("Access-Control-Allow-Methods","GET,POST,DELETE,OPTIONS")
        self.end_headers(); self.wfile.write(body)
    def _err(self, code, e): self._send(code, {"ok": False, "error": type(e).__name__, "message": str(e)})
    def _body(self):
        n=int(self.headers.get("Content-Length","0") or 0); raw=self.rfile.read(n) if n else b"{}"; return json.loads(raw) if raw else {}
    def _static(self, path):
        rel = "index.html" if path in ("/","") else path.lstrip("/")
        f=(WEB_DIR/rel).resolve()
        if WEB_DIR.resolve() not in f.parents and f!=WEB_DIR.resolve(): return False
        if not f.is_file(): return False
        ctype=mimetypes.guess_type(str(f))[0] or "application/octet-stream"
        self._send(200, f.read_bytes(), ctype + ("; charset=utf-8" if ctype.startswith("text/") or ctype=="application/javascript" else ""))
        return True
    def do_OPTIONS(self): self._send(204,b"")
    def do_GET(self):
        try:
            u=urlparse(self.path); q=parse_qs(u.query); p=u.path.rstrip("/") or "/"
            if p=="/" or p.startswith("/app"): return None if self._static("/") else self._err(404, FileNotFoundError("index.html"))
            if self._static(p): return None
            if p in ("/health","/api/health"): return self._send(200, {"ok":True,"service":"mem20energyawarecomputemigrationz"})
            if p in ("/status","/api/status"): return self._send(200, self.svc.status())
            if p=="/api/doctor": return self._send(200, self.svc.doctor())
            if p=="/api/events": return self._send(200, {"ok":True,"events":self.svc.events(int(q.get("since",["0"])[0]), int(q.get("limit",["200"])[0]))})
            if p=="/api/migrations": return self._send(200, {"ok":True,"migrations":self.svc.migrations(int(q.get("limit",["100"])[0]))})
            if p=="/api/nodes": return self._send(200, {"ok":True,"nodes":self.svc.list_nodes()})
            if p=="/api/workloads": return self._send(200, {"ok":True,"workloads":self.svc.list_workloads()})
            if p.startswith("/api/nodes/"): return self._send(200, {"ok":True,"node":self.svc.get_node(p.rsplit("/",1)[1])})
            if p.startswith("/api/workloads/"): return self._send(200, {"ok":True,"workload":self.svc.get_workload(p.rsplit("/",1)[1])})
            return self._err(404, KeyError(p))
        except NotFoundError as e: self._err(404,e)
        except Exception as e: self._err(500,e)
    def do_POST(self):
        try:
            p=urlparse(self.path).path.rstrip("/"); b=self._body() if int(self.headers.get("Content-Length","0") or 0) else {}
            if p=="/api/nodes": return self._send(200, self.svc.put_node(b))
            if p=="/api/workloads": return self._send(200, self.svc.put_workload(b))
            if p in ("/api/plan","/plan"): return self._send(200, self.svc.plan(b))
            if p in ("/api/migrate","/migrate"): return self._send(200, self.svc.migrate(str(b.get("workload_id") or b.get("id") or ""), b.get("target_node") or b.get("to")))
            if p=="/api/snapshot": return self._send(200, {"ok":True, **self.svc.snapshot(str(b.get("label") or ""))})
            if p=="/api/restore": return self._send(200, self.svc.restore(str(b.get("snapshot_id") or "")))
            if p=="/api/simulate": return self._send(200, self.svc.simulate())
            if p=="/api/benchmark": return self._send(200, self.svc.benchmark(int(b.get("iterations") or 20)))
            if p=="/execute": return self._send(200, self.svc.plan(b) if (b.get("workloads") or b.get("nodes")) else self.svc.status())
            return self._err(404, KeyError(p))
        except NotFoundError as e: self._err(404,e)
        except ConflictError as e: self._err(409,e)
        except (ValidationError, ValueError, KeyError) as e: self._err(400,e)
        except Exception as e: self._err(500,e)
    def log_message(self,*a): return

def serve(svc, host="127.0.0.1", port=8783):
    class H(Handler): pass
    H.svc = svc; return ThreadingHTTPServer((host,port), H)

def main(argv=None):
    ap=argparse.ArgumentParser(prog="mem20energyawarecomputemigrationz", description="Energy-Aware Compute Migration (RM-047)")
    ap.add_argument("--db", default="state/mem20energyawarecomputemigrationz.sqlite3")
    sub=ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status"); sub.add_parser("doctor"); sub.add_parser("simulate")
    b=sub.add_parser("benchmark"); b.add_argument("--iterations", type=int, default=20)
    n=sub.add_parser("node"); ns=n.add_subparsers(dest="node_cmd", required=True)
    na=ns.add_parser("add"); na.add_argument("--id", required=True); na.add_argument("--power", type=float, default=100); na.add_argument("--speed", type=float, default=1.0); na.add_argument("--rate", type=float, default=0.12); na.add_argument("--carbon", type=float, default=400); na.add_argument("--renewable", type=float, default=0); na.add_argument("--battery", type=float); na.add_argument("--thermal", type=float); na.add_argument("--thermal-limit", type=float, default=85); na.add_argument("--region", default="")
    ns.add_parser("list")
    w=sub.add_parser("workload"); ws=w.add_subparsers(dest="wl_cmd", required=True)
    wa=ws.add_parser("add"); wa.add_argument("--id", required=True); wa.add_argument("--size", type=float, default=1); wa.add_argument("--priority", type=int, default=1); wa.add_argument("--current-node")
    ws.add_parser("list")
    p=sub.add_parser("plan"); p.add_argument("--json")
    mg=sub.add_parser("migrate"); mg.add_argument("--workload", required=True); mg.add_argument("--to")
    e=sub.add_parser("events"); e.add_argument("--since", type=int, default=0); e.add_argument("--limit", type=int, default=50)
    sv=sub.add_parser("serve"); sv.add_argument("--host", default="127.0.0.1"); sv.add_argument("--port", type=int, default=8783)
    ex=sub.add_parser("execute"); ex.add_argument("json", nargs="?", default="{}")
    args=ap.parse_args(argv); svc=MigrationService(args.db)
    try:
        if args.cmd=="status": print(_j(svc.status()))
        elif args.cmd=="doctor": print(_j(svc.doctor()))
        elif args.cmd=="simulate": print(_j(svc.simulate()))
        elif args.cmd=="benchmark": print(_j(svc.benchmark(args.iterations)))
        elif args.cmd=="node" and args.node_cmd=="add": print(_j(svc.put_node({"node_id":args.id,"power_watts":args.power,"speed":args.speed,"energy_rate":args.rate,"carbon_g_per_kwh":args.carbon,"renewable_pct":args.renewable,"battery_pct":args.battery,"thermal_c":args.thermal,"thermal_limit_c":args.thermal_limit,"region":args.region})))
        elif args.cmd=="node": print(_j({"ok":True,"nodes":svc.list_nodes()}))
        elif args.cmd=="workload" and args.wl_cmd=="add": print(_j(svc.put_workload({"workload_id":args.id,"size":args.size,"priority":args.priority,"current_node":args.current_node})))
        elif args.cmd=="workload": print(_j({"ok":True,"workloads":svc.list_workloads()}))
        elif args.cmd=="plan": print(_j(svc.plan(_read_json(args.json) if args.json else {})))
        elif args.cmd=="migrate": print(_j(svc.migrate(args.workload, args.to)))
        elif args.cmd=="events": print(_j({"ok":True,"events":svc.events(args.since,args.limit)}))
        elif args.cmd=="serve":
            h=serve(svc,args.host,args.port); print(f"serving mem20energyawarecomputemigrationz on http://{args.host}:{h.server_address[1]}", flush=True); h.serve_forever()
        elif args.cmd=="execute":
            b=_read_json(args.json); print(_j(svc.plan(b) if (b.get("workloads") or b.get("nodes")) else svc.status()))
        else: ap.print_help(); return 2
        return 0
    except (NotFoundError, ConflictError, ValidationError, ValueError) as e:
        print(_j({"ok":False,"error":type(e).__name__,"message":str(e)})); return 1
