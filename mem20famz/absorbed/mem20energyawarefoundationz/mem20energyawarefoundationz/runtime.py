from __future__ import annotations
import argparse, json, mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from .service import FoundationService, ValidationError
from .store import ConflictError, NotFoundError
WEB_DIR=Path(__file__).with_name("web")
def _j(o): return json.dumps(o,indent=2,sort_keys=True,default=str)
def _rj(t):
    if not t: return {}
    t=t.strip(); return json.loads(Path(t[1:]).read_text()) if t.startswith("@") else json.loads(t)
class H(BaseHTTPRequestHandler):
    svc=None
    def _send(self,code,obj,ctype="application/json; charset=utf-8"):
        b=obj if isinstance(obj,(bytes,bytearray)) else _j(obj).encode(); self.send_response(code); self.send_header("Content-Type",ctype); self.send_header("Content-Length",str(len(b))); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b)
    def _err(self,code,e): self._send(code,{"ok":False,"error":type(e).__name__,"message":str(e)})
    def _body(self): n=int(self.headers.get("Content-Length","0") or 0); r=self.rfile.read(n) if n else b"{}"; return json.loads(r) if r else {}
    def _static(self,p):
        rel="index.html" if p in ("/","") else p.lstrip("/"); f=(WEB_DIR/rel).resolve()
        if WEB_DIR.resolve() not in f.parents and f!=WEB_DIR.resolve(): return False
        if not f.is_file(): return False
        ct=mimetypes.guess_type(str(f))[0] or "application/octet-stream"; self._send(200,f.read_bytes(),ct+("; charset=utf-8" if ct.startswith("text/") or ct=="application/javascript" else "")); return True
    def do_OPTIONS(self): self._send(204,b"")
    def do_GET(self):
        try:
            p=urlparse(self.path).path.rstrip("/") or "/"
            if p=="/":
                if not self._static("/"): self._err(404, FileNotFoundError("index.html"))
                return
            if self._static(p): return
            if p in ("/health","/api/health"): return self._send(200,{"ok":True})
            if p in ("/status","/api/status"): return self._send(200,self.svc.status())
            if p=="/api/doctor": return self._send(200,self.svc.doctor())
            if p=="/api/devices": return self._send(200,{"ok":True,"devices":self.svc.list_devices()})
            if p=="/api/events": q=parse_qs(urlparse(self.path).query); return self._send(200,{"ok":True,"events":self.svc.events(int(q.get("since",["0"])[0]),int(q.get("limit",["100"])[0]))})
            return self._err(404,KeyError(p))
        except Exception as e: self._err(500,e)
    def do_POST(self):
        try:
            p=urlparse(self.path).path.rstrip("/"); b=self._body() if int(self.headers.get("Content-Length","0") or 0) else {}
            if p=="/api/devices": return self._send(200,self.svc.put_device(b))
            if p=="/api/policies": return self._send(200,self.svc.put_policy(b))
            if p in ("/api/evaluate","/evaluate"): return self._send(200,self.svc.evaluate(b.get("policy_id","default"), b.get("devices")))
            if p=="/api/simulate": return self._send(200,self.svc.simulate())
            if p=="/api/benchmark": return self._send(200,self.svc.benchmark(int(b.get("iterations",20))))
            if p=="/api/snapshot": return self._send(200,{"ok":True,**self.svc.snapshot(str(b.get("label","")))})
            if p=="/api/restore": return self._send(200,self.svc.restore(str(b.get("snapshot_id",""))))
            if p=="/execute": return self._send(200,self.svc.status())
            return self._err(404,KeyError(p))
        except NotFoundError as e: self._err(404,e)
        except ConflictError as e: self._err(409,e)
        except Exception as e: self._err(400,e)
    def log_message(self,*a): return
def serve(svc,host="127.0.0.1",port=8784): HH=type("HH",(H,),{}); HH.svc=svc; return ThreadingHTTPServer((host,port),HH)
def main(argv=None):
    ap=argparse.ArgumentParser(prog="mem20energyawarefoundationz"); ap.add_argument("--db",default="state/mem20energyawarefoundationz.sqlite3")
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("status"); sub.add_parser("doctor"); sub.add_parser("simulate")
    b=sub.add_parser("benchmark"); b.add_argument("--iterations",type=int,default=20)
    d=sub.add_parser("device"); ds=d.add_subparsers(dest="dc",required=True); da=ds.add_parser("add"); da.add_argument("--id",required=True); da.add_argument("--power",type=float,default=0); da.add_argument("--max",type=float,default=0); ds.add_parser("list")
    p=sub.add_parser("policy"); p.add_argument("--id",default="default"); p.add_argument("--budget",type=float,default=0); p.add_argument("--threshold",type=float,default=0)
    e=sub.add_parser("evaluate"); e.add_argument("--policy",default="default")
    sv=sub.add_parser("serve"); sv.add_argument("--host",default="127.0.0.1"); sv.add_argument("--port",type=int,default=8784)
    ex=sub.add_parser("execute"); ex.add_argument("json",nargs="?",default="{}")
    a=ap.parse_args(argv); svc=FoundationService(a.db)
    try:
        if a.cmd=="status": print(_j(svc.status()))
        elif a.cmd=="doctor": print(_j(svc.doctor()))
        elif a.cmd=="simulate": print(_j(svc.simulate()))
        elif a.cmd=="benchmark": print(_j(svc.benchmark(a.iterations)))
        elif a.cmd=="device" and a.dc=="add": print(_j(svc.put_device({"device_id":a.id,"power_watts":a.power,"max_watts":a.max})))
        elif a.cmd=="device": print(_j({"ok":True,"devices":svc.list_devices()}))
        elif a.cmd=="policy": print(_j(svc.put_policy({"policy_id":a.id,"budget_watts":a.budget,"default_threshold_watts":a.threshold})))
        elif a.cmd=="evaluate": print(_j(svc.evaluate(a.policy)))
        elif a.cmd=="serve": h=serve(svc,a.host,a.port); print(f"serving mem20energyawarefoundationz on http://{a.host}:{h.server_address[1]}",flush=True); h.serve_forever()
        elif a.cmd=="execute": print(_j(svc.status()))
        else: ap.print_help(); return 2
        return 0
    except Exception as e: print(_j({"ok":False,"error":type(e).__name__,"message":str(e)})); return 1
