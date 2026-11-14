"""CLI and HTTP surface for mem20autonomousdealdeskz."""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import domain

__all__ = ["main", "make_server", "serve"]

_WEB_DIR = Path(__file__).resolve().parent / "web"
_CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json"}


def default_store_path() -> Path:
    env = os.environ.get("MEM20_DEALDESK_STORE")
    return Path(env).expanduser() if env else Path.home() / ".mem20" / "autonomousdealdeskz" / "state.sqlite3"


class EventStore:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with self._db() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, type TEXT, payload TEXT)")
    def _db(self):
        db = sqlite3.connect(self.path, timeout=10); db.row_factory = sqlite3.Row; return db
    def append(self, typ, payload):
        with self._lock, self._db() as db:
            db.execute("INSERT INTO events(ts,type,payload) VALUES(?,?,?)", (time.time(), typ, json.dumps(payload, default=str)))
    def list(self, since=0, limit=100):
        with self._db() as db:
            rows = db.execute("SELECT * FROM events WHERE seq>? ORDER BY seq DESC LIMIT ?", (int(since), int(limit))).fetchall()
        out = []
        for r in rows:
            try: pl = json.loads(r["payload"])
            except Exception: pl = r["payload"]
            out.append({"seq": r["seq"], "ts": r["ts"], "type": r["type"], "payload": pl})
        return out


class Service:
    def __init__(self, store_path=None):
        self.store = EventStore(store_path or default_store_path())
    def status(self, **kwargs):
        report = domain.deal_report(**kwargs)
        self.store.append("deal.report", {"ok": report.get("ok"), "price": report.get("price")})
        return report
    def doctor(self):
        res = domain.probe(); self.store.append("deal.doctor", {"ok": res.get("ok")}); return res
    def simulate(self):
        scenarios = {}
        def run(name, fn):
            try: scenarios[name] = {"ok": True, "result": fn()}
            except Exception as e: scenarios[name] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        run("price", lambda: domain.price_deal({"price": 100}, {"volume": 500}))
        run("terms", lambda: domain.terms_score({"payment_days": 15, "contract_months": 12, "auto_renew": True}))
        run("negotiate", lambda: domain.negotiate_round(100, 80, 2))
        run("report", lambda: domain.deal_report()["ok"])
        run("doctor", lambda: domain.probe()["ok"])
        out = {"ok": all(s.get("ok") for s in scenarios.values()), "scenarios": scenarios}
        self.store.append("deal.simulate", {"ok": out["ok"]}); return out


class Handler(BaseHTTPRequestHandler):
    server_version = "mem20autonomousdealdeskz"
    @property
    def service(self) -> Service: return self.server.service  # type: ignore
    def _send(self, status, body: bytes, ct):
        self.send_response(status); self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS"); self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers(); self.wfile.write(body)
    def _json(self, payload, status=200): self._send(status, json.dumps(payload, default=str).encode(), "application/json")
    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if n <= 0: return {}
        raw = self.rfile.read(n)
        p = json.loads(raw.decode() or "{}") if raw else {}
        if not isinstance(p, dict): raise ValueError("JSON body must be an object")
        return p
    def _static(self, route):
        rel = "index.html" if route in ("", "/") else route.lstrip("/")
        cand = (_WEB_DIR / rel).resolve()
        if _WEB_DIR.resolve() not in cand.parents and cand != _WEB_DIR.resolve(): self._json({"ok": False, "error": "path traversal refused"}, 400); return
        if not cand.is_file(): self._json({"ok": False, "error": f"not found: {route}"}, 404); return
        self._send(200, cand.read_bytes(), _CONTENT_TYPES.get(cand.suffix, "application/octet-stream"))
    def do_OPTIONS(self): self._send(204, b"", "text/plain")  # noqa: N802
    def do_GET(self):  # noqa: N802
        route = urlparse(self.path).path
        try:
            if not route.startswith("/api/"): self._static(route); return
            q = {k: v[-1] for k, v in parse_qs(urlparse(self.path).query).items()}
            if route == "/api/health": self._json({"ok": True, "subsystem": "mem20autonomousdealdeskz"})
            elif route == "/api/status": self._json(self.service.status())
            elif route == "/api/doctor": self._json(self.service.doctor())
            elif route == "/api/events": self._json({"ok": True, "events": self.service.store.list(int(q.get("since", 0)), int(q.get("limit", 50)))})
            else: self._json({"ok": False, "error": f"unknown route {route}"}, 404)
        except Exception as e: self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
    def do_POST(self):  # noqa: N802
        route = urlparse(self.path).path
        try:
            p = self._body()
            if route == "/api/status": self._json(self.service.status(**{k:v for k,v in p.items() if k in ("product","customer","terms","deal","demand_obs")}))
            elif route == "/api/doctor": self._json(self.service.doctor())
            elif route == "/api/simulate": self._json(self.service.simulate())
            elif route == "/api/price": self._json({"price": domain.price_deal(p.get("product",{}), p.get("customer",{}), p.get("discount_cap",0.2))})
            elif route == "/api/negotiate": self._json({"price": domain.negotiate_round(float(p.get("current",100)), float(p.get("counter",80)), int(p.get("rounds",2)))})
            else: self._json({"ok": False, "error": f"unknown route {route}"}, 404)
        except Exception as e: self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 400)
    def log_message(self, *a): pass  # noqa: A003


def make_server(host="127.0.0.1", port=0, store_path=None):
    httpd = ThreadingHTTPServer((host, port), Handler); httpd.service = Service(store_path); return httpd  # type: ignore
def serve(host="127.0.0.1", port=8782, store_path=None):
    httpd = make_server(host, port, store_path); print(f"http://{host}:{httpd.server_port}", flush=True)
    try: httpd.serve_forever()
    except KeyboardInterrupt: pass
    finally: httpd.server_close()
def main(argv=None):
    ap = argparse.ArgumentParser(prog="mem20autonomousdealdeskz", description="Autonomous Deal Desk — CLI/HTTP/cockpit")
    ap.add_argument("--store"); sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve"); s.add_argument("--host", default="127.0.0.1"); s.add_argument("--port", type=int, default=8782)
    sub.add_parser("status"); sub.add_parser("doctor"); sub.add_parser("simulate")
    args = ap.parse_args(argv); svc = Service(args.store)
    if args.cmd == "serve": serve(args.host, args.port, args.store)
    elif args.cmd == "status": print(json.dumps(svc.status(), indent=2, default=str))
    elif args.cmd == "doctor": print(json.dumps(svc.doctor(), indent=2, default=str))
    elif args.cmd == "simulate": print(json.dumps(svc.simulate(), indent=2, default=str))
    return 0
if __name__ == "__main__": sys.exit(main())
