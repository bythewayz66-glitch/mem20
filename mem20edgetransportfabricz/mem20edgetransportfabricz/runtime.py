"""CLI + JSON HTTP API + static cockpit for the edge transport fabric."""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from .service import ConflictError, NotFoundError, StoreError, TransportFabricService, ValidationError

WEB_DIR = Path(__file__).with_name("web")


def _j(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, default=str)


def _svc(args) -> TransportFabricService:
    return TransportFabricService(getattr(args, "db", None) or "state/mem20edgetransportfabricz.sqlite3")


def _read_json_arg(text: Optional[str]) -> Any:
    if not text:
        return {}
    text = text.strip()
    if text.startswith("@"):
        return json.loads(Path(text[1:]).read_text())
    return json.loads(text)


class FabricHandler(BaseHTTPRequestHandler):
    svc: TransportFabricService = None  # type: ignore[assignment]

    def _send(self, code: int, obj: Any, ctype: str = "application/json; charset=utf-8") -> None:
        body = obj if isinstance(obj, (bytes, bytearray)) else _j(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Idempotency-Key")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _err(self, code: int, e: Exception) -> None:
        self._send(code, {"ok": False, "error": type(e).__name__, "message": str(e)})

    def _body(self) -> Any:
        n = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        if not raw:
            return {}
        return json.loads(raw)

    def _static(self, path: str) -> bool:
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        f = (WEB_DIR / rel).resolve()
        if WEB_DIR.resolve() not in f.parents and f != WEB_DIR.resolve():
            return False
        if not f.is_file():
            return False
        ctype = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
        self._send(200, f.read_bytes(), ctype + ("; charset=utf-8" if ctype.startswith("text/") or ctype == "application/javascript" else ""))
        return True

    def do_OPTIONS(self):  # noqa: N802
        self._send(204, b"")

    def do_GET(self):  # noqa: N802
        try:
            u = urlparse(self.path)
            q = parse_qs(u.query)
            p = u.path.rstrip("/") or "/"
            if p == "/" or p.startswith("/app"):
                return None if self._static("/") else self._err(404, FileNotFoundError("index.html"))
            if self._static(p):
                return None
            if p in ("/health", "/api/health"): return self._send(200, {"ok": True, "service": "mem20edgetransportfabricz"})
            if p in ("/status", "/api/status"): return self._send(200, self.svc.status())
            if p == "/api/doctor": return self._send(200, self.svc.doctor())
            if p == "/api/metrics": return self._send(200, {"ok": True, "metrics": self.svc.store.metrics()})
            if p == "/api/events": return self._send(200, {"ok": True, "events": self.svc.events(int(q.get("since", ["0"])[0]), int(q.get("limit", ["200"])[0]))})
            if p == "/api/placements": return self._send(200, {"ok": True, "placements": self.svc.placements(q.get("flow_id", [None])[0], int(q.get("limit", ["100"])[0]))})
            if p == "/api/nodes": return self._send(200, {"ok": True, "nodes": self.svc.list_nodes()})
            if p == "/api/links": return self._send(200, {"ok": True, "links": self.svc.list_links()})
            if p == "/api/flows": return self._send(200, {"ok": True, "flows": self.svc.list_flows()})
            if p.startswith("/api/flows/"): return self._send(200, {"ok": True, "flow": self.svc.get_flow(p.rsplit("/", 1)[1])})
            # legacy/simple
            if p == "/metrics": return self._send(200, self.svc.store.metrics())
            if p == "/spec": return self._send(200, json.loads((Path(__file__).resolve().parents[1] / "CAPABILITY.json").read_text()))
            return self._err(404, KeyError(p))
        except NotFoundError as e: self._err(404, e)
        except (ValidationError, StoreError) as e: self._err(400, e)
        except Exception as e: self._err(500, e)

    def do_POST(self):  # noqa: N802
        try:
            p = urlparse(self.path).path.rstrip("/")
            b = self._body() if int(self.headers.get("Content-Length", "0") or 0) else {}
            idem = self.headers.get("Idempotency-Key")
            if p == "/api/nodes": return self._send(200, self.svc.put_node(b))
            if p == "/api/links": return self._send(200, self.svc.put_link(b))
            if p.startswith("/api/links/") and p.endswith("/status"):
                link_id = p[len("/api/links/"):-len("/status")]
                return self._send(200, self.svc.set_link_status(link_id, b.get("status", "up")))
            if p in ("/api/flows/admit", "/api/admit", "/execute"): return self._send(200, self.svc.admit(b, idempotency_key=idem or b.get("idempotency_key")))
            if p in ("/api/route", "/route"): return self._send(200, self.svc.route(b))
            if p == "/api/reserve": return self._send(200, self.svc.reserve(str(b.get("flow_id") or "")))
            if p == "/api/release": return self._send(200, self.svc.release(str(b.get("flow_id") or "")))
            if p == "/api/reroute": return self._send(200, self.svc.reroute(str(b.get("flow_id") or ""), b.get("avoid_links"), str(b.get("reason") or "link-failure")))
            if p == "/api/snapshot": return self._send(200, {"ok": True, **self.svc.snapshot(str(b.get("label") or ""))})
            if p == "/api/restore": return self._send(200, self.svc.restore(str(b.get("snapshot_id") or "")))
            if p == "/api/simulate": return self._send(200, self.svc.simulate())
            if p == "/api/benchmark": return self._send(200, self.svc.benchmark(int(b.get("iterations") or 20)))
            return self._err(404, KeyError(p))
        except NotFoundError as e: self._err(404, e)
        except ConflictError as e: self._err(409, e)
        except (ValidationError, StoreError, ValueError, KeyError, json.JSONDecodeError) as e: self._err(400, e)
        except Exception as e: self._err(500, e)

    def do_DELETE(self):  # noqa: N802
        try:
            p = urlparse(self.path).path.rstrip("/")
            if p.startswith("/api/nodes/"): return self._send(200, self.svc.delete_object("node", p.rsplit("/", 1)[1]))
            if p.startswith("/api/links/"): return self._send(200, self.svc.delete_object("link", p.rsplit("/", 1)[1]))
            if p.startswith("/api/flows/"): return self._send(200, self.svc.delete_object("flow", p.rsplit("/", 1)[1]))
            return self._err(404, KeyError(p))
        except NotFoundError as e: self._err(404, e)
        except Exception as e: self._err(400, e)

    def log_message(self, *a):  # noqa: D401
        return


def serve(svc: TransportFabricService, host: str = "127.0.0.1", port: int = 8782) -> ThreadingHTTPServer:
    class Handler(FabricHandler):
        pass
    Handler.svc = svc
    return ThreadingHTTPServer((host, port), Handler)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="mem20edgetransportfabricz", description="Edge Transport Fabric (RM-077)")
    ap.add_argument("--db", default="state/mem20edgetransportfabricz.sqlite3", help="SQLite state plane path")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")
    sub.add_parser("doctor")
    sub.add_parser("simulate")
    b = sub.add_parser("benchmark"); b.add_argument("--iterations", type=int, default=20)
    m = sub.add_parser("metrics")
    e = sub.add_parser("events"); e.add_argument("--since", type=int, default=0); e.add_argument("--limit", type=int, default=50)
    pl = sub.add_parser("placements"); pl.add_argument("--flow-id"); pl.add_argument("--limit", type=int, default=50)

    n = sub.add_parser("node"); ns = n.add_subparsers(dest="node_cmd", required=True)
    na = ns.add_parser("add"); na.add_argument("--id", required=True); na.add_argument("--kind", default="edge"); na.add_argument("--region", default=""); na.add_argument("--status", default="online"); na.add_argument("--capacity", type=float, default=1000.0)
    ns.add_parser("list")

    l = sub.add_parser("link"); ls = l.add_subparsers(dest="link_cmd", required=True)
    la = ls.add_parser("add"); la.add_argument("--id"); la.add_argument("--src", required=True); la.add_argument("--dst", required=True); la.add_argument("--bandwidth", type=float, default=100.0); la.add_argument("--latency", type=float, default=10.0); la.add_argument("--loss", type=float, default=0.0); la.add_argument("--jitter", type=float, default=0.0); la.add_argument("--status", default="up"); la.add_argument("--cost", type=float, default=1.0)
    ls.add_parser("list")
    lss = ls.add_parser("set-status"); lss.add_argument("link_id"); lss.add_argument("--status", required=True)

    f = sub.add_parser("flow"); fs = f.add_subparsers(dest="flow_cmd", required=True)
    fa = fs.add_parser("admit"); fa.add_argument("--json", help="flow JSON or @file"); fa.add_argument("--id"); fa.add_argument("--src"); fa.add_argument("--dst"); fa.add_argument("--demand", type=float, default=1.0); fa.add_argument("--priority", type=int, default=1); fa.add_argument("--max-latency", type=float); fa.add_argument("--intermittent-ok", action="store_true", default=True); fa.add_argument("--idempotency-key")
    fr = fs.add_parser("route"); fr.add_argument("--json"); fr.add_argument("--src"); fr.add_argument("--dst"); fr.add_argument("--demand", type=float, default=1.0); fr.add_argument("--priority", type=int, default=1)
    fg = fs.add_parser("get"); fg.add_argument("flow_id")
    fs.add_parser("list")
    fres = fs.add_parser("reserve"); fres.add_argument("flow_id")
    frel = fs.add_parser("release"); frel.add_argument("flow_id")
    frr = fs.add_parser("reroute"); frr.add_argument("flow_id"); frr.add_argument("--avoid", default=""); frr.add_argument("--reason", default="link-failure")

    sn = sub.add_parser("snapshot"); sn.add_argument("--label", default="")
    rs = sub.add_parser("restore"); rs.add_argument("snapshot_id")

    sv = sub.add_parser("serve"); sv.add_argument("--host", default="127.0.0.1"); sv.add_argument("--port", type=int, default=8782)

    # legacy-compatible commands
    ex = sub.add_parser("execute"); ex.add_argument("json", nargs="?", default="{}"); ex.add_argument("--idem")
    sub.add_parser("mesh")
    return ap


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        svc = _svc(args)
        if args.cmd == "status": print(_j(svc.status())); return 0
        if args.cmd == "doctor": print(_j(svc.doctor())); return 0
        if args.cmd == "simulate": print(_j(svc.simulate())); return 0
        if args.cmd == "benchmark": print(_j(svc.benchmark(args.iterations))); return 0
        if args.cmd == "metrics": print(_j({"ok": True, "metrics": svc.store.metrics()})); return 0
        if args.cmd == "events": print(_j({"ok": True, "events": svc.events(args.since, args.limit)})); return 0
        if args.cmd == "placements": print(_j({"ok": True, "placements": svc.placements(args.flow_id, args.limit)})); return 0
        if args.cmd == "node":
            if args.node_cmd == "add":
                print(_j(svc.put_node({"node_id": args.id, "kind": args.kind, "region": args.region, "status": args.status, "capacity_mbps": args.capacity}))); return 0
            print(_j({"ok": True, "nodes": svc.list_nodes()})); return 0
        if args.cmd == "link":
            if args.link_cmd == "add":
                print(_j(svc.put_link({"link_id": args.id, "src": args.src, "dst": args.dst, "bandwidth_mbps": args.bandwidth, "latency_ms": args.latency, "loss_rate": args.loss, "jitter_ms": args.jitter, "status": args.status, "cost": args.cost}))); return 0
            if args.link_cmd == "set-status":
                print(_j(svc.set_link_status(args.link_id, args.status))); return 0
            print(_j({"ok": True, "links": svc.list_links()})); return 0
        if args.cmd == "flow":
            if args.flow_cmd == "admit":
                payload = _read_json_arg(args.json) if args.json else {}
                if args.src: payload.setdefault("src", args.src)
                if args.dst: payload.setdefault("dst", args.dst)
                if args.id: payload.setdefault("flow_id", args.id)
                payload.setdefault("demand_mbps", args.demand); payload.setdefault("priority", args.priority)
                if args.max_latency is not None: payload.setdefault("max_latency_ms", args.max_latency)
                payload.setdefault("intermittent_ok", args.intermittent_ok)
                print(_j(svc.admit(payload, idempotency_key=args.idempotency_key))); return 0
            if args.flow_cmd == "route":
                payload = _read_json_arg(args.json) if args.json else {}
                if args.src: payload.setdefault("src", args.src)
                if args.dst: payload.setdefault("dst", args.dst)
                payload.setdefault("demand_mbps", args.demand); payload.setdefault("priority", args.priority)
                print(_j(svc.route(payload))); return 0
            if args.flow_cmd == "get": print(_j({"ok": True, "flow": svc.get_flow(args.flow_id)})); return 0
            if args.flow_cmd == "reserve": print(_j(svc.reserve(args.flow_id))); return 0
            if args.flow_cmd == "release": print(_j(svc.release(args.flow_id))); return 0
            if args.flow_cmd == "reroute": print(_j(svc.reroute(args.flow_id, [x for x in args.avoid.split(",") if x], args.reason))); return 0
            print(_j({"ok": True, "flows": svc.list_flows()})); return 0
        if args.cmd == "snapshot": print(_j({"ok": True, **svc.snapshot(args.label)})); return 0
        if args.cmd == "restore": print(_j(svc.restore(args.snapshot_id))); return 0
        if args.cmd == "serve":
            httpd = serve(svc, args.host, args.port)
            print(f"serving mem20edgetransportfabricz on http://{args.host}:{httpd.server_address[1]}", flush=True)
            httpd.serve_forever(); return 0
        if args.cmd == "execute":
            # legacy compatibility: admit/route when src/dst present, else status
            payload = _read_json_arg(args.json)
            if payload.get("src") and payload.get("dst"):
                print(_j(svc.admit(payload, idempotency_key=args.idem))); return 0
            print(_j(svc.status())); return 0
        if args.cmd == "mesh":
            print(_j(svc.doctor())); return 0
        ap = build_parser(); ap.print_help(); return 2
    except NotFoundError as e:
        print(_j({"ok": False, "error": "NotFoundError", "message": str(e)})); return 3
    except ConflictError as e:
        print(_j({"ok": False, "error": "ConflictError", "message": str(e)})); return 4
    except (ValidationError, StoreError, ValueError, KeyError) as e:
        print(_j({"ok": False, "error": type(e).__name__, "message": str(e)})); return 1
