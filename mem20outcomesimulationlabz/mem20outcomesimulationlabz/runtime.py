"""CLI and HTTP surface for mem20outcomesimulationlabz."""
from __future__ import annotations
import argparse,json,os,sqlite3,sys,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from . import domain
_WEB_DIR=Path(__file__).resolve().parent/"web"; _CT={".html":"text/html; charset=utf-8",".js":"text/javascript; charset=utf-8",".css":"text/css; charset=utf-8",".json":"application/json"}
def default_store_path(): e=os.environ.get("MEM20_OUTSIM_STORE"); return Path(e).expanduser() if e else Path.home()/".mem20"/"mem20outcomesimulationlabz"/"state.sqlite3"
class EventStore:
    def __init__(self,path): self.path=str(path); Path(self.path).parent.mkdir(parents=True,exist_ok=True); self._lock=threading.RLock(); self._init()
    def _db(self): db=sqlite3.connect(self.path,timeout=10); db.row_factory=sqlite3.Row; return db
    def _init(self):
        with self._db() as db: db.execute("PRAGMA journal_mode=WAL"); db.execute("CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,ts REAL,type TEXT,payload TEXT)")
    def append(self,typ,payload):
        with self._lock,self._db() as db: db.execute("INSERT INTO events(ts,type,payload) VALUES(?,?,?)",(time.time(),typ,json.dumps(payload,default=str)))
    def list(self,since=0,limit=100):
        with self._db() as db: rows=db.execute("SELECT * FROM events WHERE seq>? ORDER BY seq DESC LIMIT ?",(int(since),int(limit))).fetchall()
        return [{"seq":r["seq"],"ts":r["ts"],"type":r["type"],"payload":json.loads(r["payload"])} for r in rows]
class Service:
    def __init__(self,store_path=None): self.store=EventStore(store_path or default_store_path())
    def status(self,**kw): r=domain.simulation_report(**kw); self.store.append("report",{"ok":r.get("ok")}); return r
    def doctor(self): r=domain.probe(); self.store.append("doctor",{"ok":r.get("ok")}); return r
    def simulate(self): r={"ok":bool(domain.simulation_report().get("ok") and domain.probe().get("ok"))}; self.store.append("simulate",r); return r
class Handler(BaseHTTPRequestHandler):
    server_version="mem20outcomesimulationlabz"
    @property
    def service(self)->Service: return self.server.service  # type: ignore
    def _send(self,st,body,ct): self.send_response(st); self.send_header("Content-Type",ct); self.send_header("Content-Length",str(len(body))); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(body)
    def _json(self,p,st=200): self._send(st,json.dumps(p,default=str).encode(),"application/json")
    def _body(self): n=int(self.headers.get("Content-Length",0) or 0); p=json.loads(self.rfile.read(n).decode() or "{}") if n else {}; 
    def _static(self,route):
        rel="index.html" if route in ("","/") else route.lstrip("/"); cand=(_WEB_DIR/rel).resolve()
        if _WEB_DIR.resolve() not in cand.parents and cand!=_WEB_DIR.resolve(): self._json({"ok":False},400); return
        if not cand.is_file(): self._json({"ok":False},404); return
        self._send(200,cand.read_bytes(),_CT.get(cand.suffix,"application/octet-stream"))
    def do_OPTIONS(self): self._send(204,b"","text/plain")  # noqa
    def do_GET(self):  # noqa
        route=urlparse(self.path).path
        try:
            if not route.startswith("/api/"): self._static(route); return
            if route=="/api/health": self._json({"ok":True})
            elif route=="/api/status": self._json(self.service.status())
            elif route=="/api/doctor": self._json(self.service.doctor())
            elif route=="/api/events": self._json({"ok":True,"events":self.service.store.list()})
            else: self._json({"ok":False},404)
        except Exception as e: self._json({"ok":False,"error":f"{type(e).__name__}: {e}"},500)
    def do_POST(self):  # noqa
        route=urlparse(self.path).path
        try:
            n=int(self.headers.get("Content-Length",0) or 0); p=json.loads(self.rfile.read(n).decode() or "{}") if n else {}
            if route=="/api/status": self._json(self.service.status(**(p if isinstance(p,dict) else {})))
            elif route=="/api/doctor": self._json(self.service.doctor())
            elif route=="/api/simulate": self._json(self.service.simulate())
            else: self._json({"ok":False},404)
        except Exception as e: self._json({"ok":False,"error":f"{type(e).__name__}: {e}"},400)
    def log_message(self,*a): pass  # noqa
def make_server(host="127.0.0.1",port=0,store_path=None): h=ThreadingHTTPServer((host,port),Handler); h.service=Service(store_path); return h  # type: ignore
def serve(host="127.0.0.1",port=8850,store_path=None):
    h=make_server(host,port,store_path); print(f"http://{host}:{h.server_port}",flush=True)
    try: h.serve_forever()
    except KeyboardInterrupt: pass
    finally: h.server_close()
def main(argv=None):
    ap=argparse.ArgumentParser(prog="mem20outcomesimulationlabz"); ap.add_argument("--store"); sub=ap.add_subparsers(dest="cmd",required=True)
    s=sub.add_parser("serve"); s.add_argument("--host",default="127.0.0.1"); s.add_argument("--port",type=int,default=8850)
    sub.add_parser("status"); sub.add_parser("doctor"); sub.add_parser("simulate")
    args=ap.parse_args(argv); svc=Service(args.store)
    if args.cmd=="serve": serve(args.host,args.port,args.store)
    elif args.cmd=="status": print(json.dumps(svc.status(),indent=2,default=str))
    elif args.cmd=="doctor": print(json.dumps(svc.doctor(),indent=2,default=str))
    elif args.cmd=="simulate": print(json.dumps(svc.simulate(),indent=2,default=str))
    return 0
if __name__=="__main__": sys.exit(main())
