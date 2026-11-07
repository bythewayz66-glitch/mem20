"""CLI and HTTP surface for the edge-to-cloud intelligence continuum."""
from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from . import domain
from .service import ContinuumService, ConflictError, NotFoundError, ValidationError

WEB_DIR = Path(__file__).resolve().parent / "web"
MIME = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8",
        ".svg": "image/svg+xml"}


def _json(data: Any) -> bytes:
    return json.dumps(data, indent=2, default=str).encode("utf-8")


def _status_for(exc: Exception) -> int:
    if isinstance(exc, ValidationError):
        return 400
    if isinstance(exc, NotFoundError):
        return 404
    if isinstance(exc, ConflictError):
        return 409
    return 500


class Handler(BaseHTTPRequestHandler):
    service: ContinuumService

    def log_message(self, fmt, *args):  # noqa: A003
        return

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send(self, status: int, body: bytes, content_type: str = "application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _error(self, exc: Exception):
        status = _status_for(exc)
        self._send(status, _json({"ok": False, "error": str(exc), "type": type(exc).__name__}))

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        if not raw:
            return {}
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise ValidationError(f"invalid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ValidationError("JSON body must be an object")
        return data

    def _serve_static(self, path: str):
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        target = (WEB_DIR / rel).resolve()
        web_root = WEB_DIR.resolve()
        if web_root != target and web_root not in target.parents:
            self._send(403, b"forbidden", "text/plain; charset=utf-8")
            return
        if not target.is_file():
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        self._send(200, target.read_bytes(), MIME.get(target.suffix.lower(), "application/octet-stream"))

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):  # noqa: N802
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            q = parse_qs(parsed.query)
            if not path.startswith("/api"):
                self._serve_static(path)
                return
            if path == "/api/status":
                self._send(200, _json(self.service.status()))
            elif path == "/api/targets":
                self._send(200, _json({"ok": True, "targets": self.service.list_targets()}))
            elif path.startswith("/api/targets/"):
                tid = path.rsplit("/", 1)[-1]
                self._send(200, _json({"ok": True, "target": self.service.get_target(tid)}))
            elif path == "/api/workloads":
                state = (q.get("state") or [None])[0]
                self._send(200, _json({"ok": True, "workloads": self.service.list_workloads(state)}))
            elif path.startswith("/api/workloads/"):
                wid = path.rsplit("/", 1)[-1]
                self._send(200, _json({"ok": True, "workload": self.service.get_workload(wid)}))
            elif path == "/api/events":
                since = int((q.get("since") or ["0"])[0])
                limit = int((q.get("limit") or ["200"])[0])
                self._send(200, _json({"ok": True, "events": self.service.events(since, limit)}))
            elif path == "/api/placements":
                wid = (q.get("workload_id") or [None])[0]
                self._send(200, _json({"ok": True, "placements": self.service.store.list_placements(wid)}))
            elif path == "/api/migrations":
                self._send(200, _json({"ok": True, "migrations": self.service.store.list_migrations()}))
            elif path == "/api/metrics":
                self._send(200, _json({"ok": True, "metrics": self.service.metrics()}))
            elif path == "/api/doctor":
                self._send(200, _json(self.service.doctor()))
            elif path == "/api/benchmark":
                n = int((q.get("iterations") or ["20"])[0])
                self._send(200, _json(self.service.benchmark(n)))
            else:
                self._send(404, _json({"ok": False, "error": f"unknown route: {path}"}))
        except Exception as exc:  # noqa: BLE001
            self._error(exc)

    def do_POST(self):  # noqa: N802
        try:
            path = urlparse(self.path).path
            body = self._read_json()
            if path == "/api/targets":
                self._send(200, _json(self.service.register_target(body)))
            elif path == "/api/workloads":
                self._send(200, _json(self.service.submit_workload(body)))
            elif path == "/api/dispatch":
                self._send(200, _json(self.service.dispatch(body.get("workload_id"), body.get("limit"))))
            elif path == "/api/place":
                self._send(200, _json(self.service.place(body["workload_id"])))
            elif path == "/api/complete":
                self._send(200, _json(self.service.complete(body["workload_id"], success=body.get("success", True), reason=body.get("reason", ""))))
            elif path == "/api/failover":
                self._send(200, _json(self.service.failover(body["workload_id"], reason=body.get("reason", "failover requested"))))
            elif path == "/api/migrations/plan":
                self._send(200, _json(self.service.plan_migrations(float(body.get("load_threshold", 0.85)))))
            elif path == "/api/snapshot":
                self._send(200, _json(self.service.snapshot(body.get("label", ""))))
            elif path == "/api/restore":
                self._send(200, _json(self.service.restore(body["snapshot_id"])))
            elif path == "/api/simulate":
                self._send(200, _json(self.service.simulate()))
            elif path.startswith("/api/targets/") and path.endswith("/status"):
                tid = path.split("/")[-2]
                self._send(200, _json(self.service.set_target_status(tid, body["status"])))
            else:
                self._send(404, _json({"ok": False, "error": f"unknown route: {path}"}))
        except Exception as exc:  # noqa: BLE001
            self._error(exc)

    def do_DELETE(self):  # noqa: N802
        try:
            path = urlparse(self.path).path
            if path.startswith("/api/targets/"):
                tid = path.rsplit("/", 1)[-1]
                self._send(200, _json(self.service.delete_target(tid)))
            else:
                self._send(404, _json({"ok": False, "error": f"unknown route: {path}"}))
        except Exception as exc:  # noqa: BLE001
            self._error(exc)


def serve(service: ContinuumService, host: str = "127.0.0.1", port: int = 8791) -> ThreadingHTTPServer:
    Handler.service = service
    httpd = ThreadingHTTPServer((host, port), Handler)
    return httpd


def _print(data: Any):
    print(json.dumps(data, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mem20edgetocloudintelligencecontinuumz")
    parser.add_argument("--store", default=None, help="SQLite store path")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("doctor")
    sub.add_parser("simulate")
    b = sub.add_parser("benchmark"); b.add_argument("--iterations", type=int, default=20)
    sub.add_parser("metrics")
    e = sub.add_parser("events"); e.add_argument("--since", type=int, default=0); e.add_argument("--limit", type=int, default=100)

    t = sub.add_parser("target"); ts = t.add_subparsers(dest="target_cmd", required=True)
    ta = ts.add_parser("add"); ta.add_argument("--id", dest="target_id"); ta.add_argument("--tier", default="edge"); ta.add_argument("--cpu", type=float, default=4); ta.add_argument("--memory", type=float, default=8); ta.add_argument("--latency", type=float, default=20); ta.add_argument("--bandwidth", type=float, default=100); ta.add_argument("--cost", type=float, default=0); ta.add_argument("--egress", type=float, default=0); ta.add_argument("--reliability", type=float, default=0.99); ta.add_argument("--capabilities", default="compute"); ta.add_argument("--privacy-zones", default="public"); ta.add_argument("--region", default="default")
    ts.add_parser("list")
    tg = ts.add_parser("get"); tg.add_argument("target_id")
    tst = ts.add_parser("status"); tst.add_argument("target_id"); tst.add_argument("status")
    td = ts.add_parser("delete"); td.add_argument("target_id")

    w = sub.add_parser("workload"); ws = w.add_subparsers(dest="workload_cmd", required=True)
    wa = ws.add_parser("submit"); wa.add_argument("--id", dest="workload_id"); wa.add_argument("--cpu", type=float, default=1); wa.add_argument("--memory", type=float, default=1); wa.add_argument("--size", type=float, default=10); wa.add_argument("--duration", type=float, default=60); wa.add_argument("--max-latency", type=float); wa.add_argument("--max-cost", type=float); wa.add_argument("--privacy-zone", default="public"); wa.add_argument("--capabilities", default="compute"); wa.add_argument("--preferred-tiers", default=""); wa.add_argument("--resilience", default="standard"); wa.add_argument("--priority", type=int, default=50); wa.add_argument("--idempotency-key", default="")
    wl = ws.add_parser("list"); wl.add_argument("--state")
    wg = ws.add_parser("get"); wg.add_argument("workload_id")
    wc = ws.add_parser("complete"); wc.add_argument("workload_id"); wc.add_argument("--fail", action="store_true"); wc.add_argument("--reason", default="")

    d = sub.add_parser("dispatch"); d.add_argument("--id", dest="workload_id"); d.add_argument("--limit", type=int)
    p = sub.add_parser("place"); p.add_argument("workload_id")
    f = sub.add_parser("failover"); f.add_argument("workload_id"); f.add_argument("--reason", default="failover requested")
    mp = sub.add_parser("migrations-plan"); mp.add_argument("--threshold", type=float, default=0.85)
    sn = sub.add_parser("snapshot"); sn.add_argument("--label", default="")
    rs = sub.add_parser("restore"); rs.add_argument("snapshot_id")
    sv = sub.add_parser("serve"); sv.add_argument("--host", default="127.0.0.1"); sv.add_argument("--port", type=int, default=8791)

    args = parser.parse_args(argv)
    svc = ContinuumService(args.store)
    try:
        if args.cmd == "status": _print(svc.status())
        elif args.cmd == "doctor": _print(svc.doctor())
        elif args.cmd == "simulate": _print(svc.simulate())
        elif args.cmd == "benchmark": _print(svc.benchmark(args.iterations))
        elif args.cmd == "metrics": _print({"ok": True, "metrics": svc.metrics()})
        elif args.cmd == "events": _print({"ok": True, "events": svc.events(args.since, args.limit)})
        elif args.cmd == "target":
            if args.target_cmd == "add":
                _print(svc.register_target({"target_id": args.target_id, "tier": args.tier, "cpu": args.cpu, "memory_gb": args.memory, "latency_ms": args.latency, "bandwidth_mbps": args.bandwidth, "cost_per_cpu_hour": args.cost, "egress_cost_per_gb": args.egress, "reliability": args.reliability, "capabilities": args.capabilities, "privacy_zones": args.privacy_zones, "region": args.region}))
            elif args.target_cmd == "list": _print({"ok": True, "targets": svc.list_targets()})
            elif args.target_cmd == "get": _print({"ok": True, "target": svc.get_target(args.target_id)})
            elif args.target_cmd == "status": _print(svc.set_target_status(args.target_id, args.status))
            elif args.target_cmd == "delete": _print(svc.delete_target(args.target_id))
        elif args.cmd == "workload":
            if args.workload_cmd == "submit":
                _print(svc.submit_workload({"workload_id": args.workload_id, "cpu": args.cpu, "memory_gb": args.memory, "size_mb": args.size, "duration_s": args.duration, "max_latency_ms": args.max_latency, "max_cost": args.max_cost, "privacy_zone": args.privacy_zone, "required_capabilities": args.capabilities, "preferred_tiers": args.preferred_tiers, "resilience": args.resilience, "priority": args.priority, "idempotency_key": args.idempotency_key}))
            elif args.workload_cmd == "list": _print({"ok": True, "workloads": svc.list_workloads(args.state)})
            elif args.workload_cmd == "get": _print({"ok": True, "workload": svc.get_workload(args.workload_id)})
            elif args.workload_cmd == "complete": _print(svc.complete(args.workload_id, success=not args.fail, reason=args.reason))
        elif args.cmd == "dispatch": _print(svc.dispatch(args.workload_id, args.limit))
        elif args.cmd == "place": _print(svc.place(args.workload_id))
        elif args.cmd == "failover": _print(svc.failover(args.workload_id, args.reason))
        elif args.cmd == "migrations-plan": _print(svc.plan_migrations(args.threshold))
        elif args.cmd == "snapshot": _print(svc.snapshot(args.label))
        elif args.cmd == "restore": _print(svc.restore(args.snapshot_id))
        elif args.cmd == "serve":
            httpd = serve(svc, args.host, args.port)
            print(f"serving on http://{args.host}:{args.port}", file=sys.stderr)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                httpd.server_close()
        else:
            parser.error(f"unknown command: {args.cmd}")
        return 0
    except Exception as exc:  # noqa: BLE001
        _print({"ok": False, "error": str(exc), "type": type(exc).__name__})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
