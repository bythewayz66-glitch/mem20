"""CLI and HTTP surface for mem20audiovoiceandmusicpipelinez.

Serves a real operator cockpit (web/) and a JSON API backed by the audio
domain and 6 subsystem-specific peer integrations (ecosystem). Durable local
event log via SQLite WAL for operator visibility.
"""
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
_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json",
    ".svg": "image/svg+xml",
}


def default_store_path() -> Path:
    env = os.environ.get("MEM20_AVMP_STORE")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".mem20" / "audiovoiceandmusicpipelinez" / "state.sqlite3"


class EventStore:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with self._db() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, type TEXT, payload TEXT)")

    def _db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def append(self, typ, payload):
        with self._lock, self._db() as db:
            db.execute("INSERT INTO events(ts,type,payload) VALUES(?,?,?)", (time.time(), typ, json.dumps(payload, default=str)))

    def list(self, since=0, limit=100):
        with self._db() as db:
            rows = db.execute("SELECT * FROM events WHERE seq>? ORDER BY seq DESC LIMIT ?", (int(since), int(limit))).fetchall()
        out = []
        for r in rows:
            try:
                pl = json.loads(r["payload"])
            except Exception:
                pl = r["payload"]
            out.append({"seq": r["seq"], "ts": r["ts"], "type": r["type"], "payload": pl})
        return out


class Service:
    def __init__(self, store_path=None):
        self.store = EventStore(store_path or default_store_path())

    def status(self, prompt="bind audio", bpm=120):
        report = domain.pipeline_report(prompt=prompt, bpm=bpm)
        self.store.append("pipeline.report", {"ok": report.get("ok"), "peers": list(report.get("peers", {}).keys())})
        return report

    def doctor(self):
        res = domain.probe()
        self.store.append("pipeline.doctor", {"ok": res.get("ok")})
        return res

    def simulate(self):
        scenarios = {}
        def run(name, fn):
            try:
                v = fn()
                scenarios[name] = {"ok": True, "result": v}
            except Exception as e:  # noqa: BLE001
                scenarios[name] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        run("mix", lambda: domain.mix_tracks([{"id": "a", "samples": [0.1, 0.2]}])["master_gain"])
        run("normalize", lambda: len(domain.normalize([0.5, 1.0])))
        run("master", lambda: len(domain.mastering_chain(["limit"], [1.2, -1.1])))
        run("report", lambda: domain.pipeline_report(prompt="sim")["ok"])
        run("doctor", lambda: domain.probe()["ok"])
        out = {"ok": all(s.get("ok") for s in scenarios.values()), "scenarios": scenarios}
        self.store.append("pipeline.simulate", {"ok": out["ok"]})
        return out

    def mix(self, tracks, volumes=None):
        res = domain.mix_tracks(tracks, volumes)
        self.store.append("pipeline.mix", {"tracks": len(res.get("tracks", []))})
        return res

    def master(self, stages, audio):
        res = domain.mastering_chain(stages, audio)
        self.store.append("pipeline.master", {"stages": stages, "samples": len(audio or [])})
        return {"stages": stages, "samples": res}


class Handler(BaseHTTPRequestHandler):
    server_version = "mem20audiovoiceandmusicpipelinez"
    protocol_version = "HTTP/1.1"

    @property
    def service(self) -> Service:
        return self.server.service  # type: ignore[attr-defined]

    def _send(self, status, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, status=200):
        self._send(status, json.dumps(payload, default=str).encode("utf-8"), "application/json")

    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if n <= 0:
            return {}
        raw = self.rfile.read(n)
        if not raw:
            return {}
        try:
            p = json.loads(raw.decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            raise ValueError(f"invalid JSON: {e}") from e
        if not isinstance(p, dict):
            raise ValueError("JSON body must be an object")
        return p

    def _static(self, route):
        rel = "index.html" if route in ("", "/") else route.lstrip("/")
        cand = (_WEB_DIR / rel).resolve()
        if _WEB_DIR.resolve() not in cand.parents and cand != _WEB_DIR.resolve():
            self._json({"ok": False, "error": "path traversal refused"}, 400)
            return
        if not cand.is_file():
            self._json({"ok": False, "error": f"not found: {route}"}, 404)
            return
        self._send(200, cand.read_bytes(), _CONTENT_TYPES.get(cand.suffix, "application/octet-stream"))

    def do_OPTIONS(self):  # noqa: N802
        self._send(204, b"", "text/plain")

    def do_GET(self):  # noqa: N802
        route = urlparse(self.path).path
        try:
            if not route.startswith("/api/"):
                self._static(route)
                return
            q = {k: v[-1] for k, v in parse_qs(urlparse(self.path).query).items()}
            if route == "/api/health":
                self._json({"ok": True, "subsystem": "mem20audiovoiceandmusicpipelinez"})
            elif route == "/api/status":
                self._json(self.service.status(q.get("prompt", "bind audio"), float(q.get("bpm", 120))))
            elif route == "/api/doctor":
                self._json(self.service.doctor())
            elif route == "/api/events":
                self._json({"ok": True, "events": self.service.store.list(int(q.get("since", 0)), int(q.get("limit", 50)))})
            else:
                self._json({"ok": False, "error": f"unknown route {route}"}, 404)
        except Exception as e:  # noqa: BLE001
            self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)

    def do_POST(self):  # noqa: N802
        route = urlparse(self.path).path
        try:
            p = self._body()
            if route == "/api/status":
                self._json(self.service.status(p.get("prompt", "bind audio"), float(p.get("bpm", 120))))
            elif route == "/api/doctor":
                self._json(self.service.doctor())
            elif route == "/api/simulate":
                self._json(self.service.simulate())
            elif route == "/api/mix":
                self._json(self.service.mix(p.get("tracks", []), p.get("volumes")))
            elif route == "/api/master":
                self._json(self.service.master(p.get("stages", []), p.get("audio", [])))
            else:
                self._json({"ok": False, "error": f"unknown route {route}"}, 404)
        except ValueError as e:
            self._json({"ok": False, "error": str(e)}, 400)
        except Exception as e:  # noqa: BLE001
            self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)

    def log_message(self, *args):  # noqa: A003
        pass


def make_server(host="127.0.0.1", port=0, store_path=None):
    svc = Service(store_path)
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.service = svc  # type: ignore[attr-defined]
    return httpd


def serve(host="127.0.0.1", port=8781, store_path=None):
    httpd = make_server(host, port, store_path)
    print(f"http://{host}:{httpd.server_port}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mem20audiovoiceandmusicpipelinez", description="Audio/Voice/Music Pipeline — CLI/HTTP/cockpit")
    ap.add_argument("--store", help="SQLite state path")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve"); s.add_argument("--host", default="127.0.0.1"); s.add_argument("--port", type=int, default=8781)
    sub.add_parser("status")
    sub.add_parser("doctor")
    sub.add_parser("simulate")
    m = sub.add_parser("mix"); m.add_argument("tracks_json")
    ms = sub.add_parser("master"); ms.add_argument("--stages", default="limit"); ms.add_argument("--audio", required=True)
    args = ap.parse_args(argv)
    svc = Service(args.store)
    if args.cmd == "serve":
        serve(args.host, args.port, args.store)
    elif args.cmd == "status":
        print(json.dumps(svc.status(), indent=2, default=str))
    elif args.cmd == "doctor":
        print(json.dumps(svc.doctor(), indent=2, default=str))
    elif args.cmd == "simulate":
        print(json.dumps(svc.simulate(), indent=2, default=str))
    elif args.cmd == "mix":
        print(json.dumps(svc.mix(json.loads(args.tracks_json)), indent=2, default=str))
    elif args.cmd == "master":
        stages = [x.strip() for x in args.stages.split(",") if x.strip()]
        audio = [float(x) for x in args.audio.split(",") if x.strip()]
        print(json.dumps(svc.master(stages, audio), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
