"""CLI and HTTP surface for the edge fleet brain.

Two ways in, one implementation: the CLI and the HTTP server both call
:class:`mem20causalroutingbrainz.service.FleetService`, so a placement made from
the terminal is the same placement made from the cockpit.

HTTP is a plain ``ThreadingHTTPServer`` with a JSON API and a static cockpit
served from ``web/``. Errors are mapped to real status codes instead of a
generic 200: validation is 400, a missing object is 404, a version race is 409,
and an unhandled failure is 500 with the exception named.

The cockpit at ``GET /`` is served by the same process, so the fleet page
always talks to the process that owns the store. ``docs/app/fleet/`` embeds the
same page against a configurable API base for the estate shell.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .domain import DeviceKind, NodeStatus
from .service import FleetService, ValidationError
from .store import ConflictError, NotFoundError

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
    env = os.environ.get("MEM20_EDGEFLEET_STORE")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".mem20" / "edgefleet" / "fleet.db"


def _service(args) -> FleetService:
    return FleetService(args.store)


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------
class _Handler(BaseHTTPRequestHandler):
    server_version = "mem20causalroutingbrainz"
    protocol_version = "HTTP/1.1"

    # -- responses ----------------------------------------------------
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, status: int = 200) -> None:
        body = json.dumps(payload, default=str, sort_keys=True).encode("utf-8")
        self._send(status, body, "application/json")

    def _error(self, exc: BaseException) -> None:
        if isinstance(exc, ValidationError):
            self._json({"ok": False, "error": str(exc), "kind": "validation"}, 400)
        elif isinstance(exc, NotFoundError):
            self._json({"ok": False, "error": f"not found: {exc}", "kind": "not_found"}, 404)
        elif isinstance(exc, ConflictError):
            self._json({"ok": False, "error": str(exc), "kind": "conflict"}, 409)
        else:
            self._json({"ok": False, "error": f"{type(exc).__name__}: {exc}",
                        "kind": "internal"}, 500)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
        except ValueError as exc:
            raise ValidationError(f"invalid JSON body: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValidationError("JSON body must be an object")
        return payload

    def _query(self) -> dict:
        parsed = urlparse(self.path)
        return {key: values[-1] for key, values in parse_qs(parsed.query).items()}

    @property
    def service(self) -> FleetService:
        return self.server.service  # type: ignore[attr-defined]

    # -- static -------------------------------------------------------
    def _static(self, route: str) -> None:
        relative = "index.html" if route in ("", "/") else route.lstrip("/")
        candidate = (_WEB_DIR / relative).resolve()
        if _WEB_DIR.resolve() not in candidate.parents and candidate != _WEB_DIR.resolve():
            self._json({"ok": False, "error": "path traversal refused"}, 400)
            return
        if not candidate.is_file():
            self._json({"ok": False, "error": f"not found: {route}"}, 404)
            return
        self._send(200, candidate.read_bytes(),
                   _CONTENT_TYPES.get(candidate.suffix, "application/octet-stream"))

    # -- verbs --------------------------------------------------------
    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(204, b"", "text/plain")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        route = parsed.path
        try:
            if not route.startswith("/api/"):
                self._static(route)
                return
            query = self._query()
            if route == "/api/status":
                self._json(self.service.status())
            elif route == "/api/healthz":
                self._json({"ok": True, "health": self.service.health()})
            elif route == "/api/nodes":
                self._json({"ok": True, "nodes": self.service.list_nodes()})
            elif route == "/api/workloads":
                self._json({"ok": True, "workloads": self.service.list_workloads(
                    query.get("state"))})
            elif route.startswith("/api/workloads/"):
                workload_id = route.split("/", 3)[3]
                self._json({"ok": True, "workload": self.service.get_workload(workload_id)})
            elif route == "/api/events":
                since = int(query.get("since", 0))
                limit = int(query.get("limit", 200))
                self._json({"ok": True, "events": self.service.events(since, limit)})
            elif route == "/api/metrics":
                self._json({"ok": True, "metrics": self.service.metrics()})
            elif route == "/api/predict":
                horizon = float(query.get("horizon_s", 3600.0))
                self._json({"ok": True, "forecasts": self.service.predict(horizon)})
            elif route == "/api/energy":
                hours = float(query.get("hours", 24.0))
                self._json({"ok": True, "energy": self.service.energy(hours)})
            elif route == "/api/doctor":
                self._json(self.service.doctor())
            elif route == "/api/benchmark":
                iterations = int(query.get("iterations", 20))
                self._json(self.service.benchmark(iterations))
            else:
                self._json({"ok": False, "error": f"unknown route {route}"}, 404)
        except Exception as exc:  # noqa: BLE001 - mapped to a status code
            self._error(exc)

    def do_POST(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        try:
            payload = self._body()
            if route == "/api/nodes":
                self._json(self.service.register_node(payload), 201)
            elif route == "/api/workloads":
                self._json(self.service.submit_workload(payload), 201)
            elif route == "/api/dispatch":
                self._json(self.service.dispatch(
                    payload.get("workload_id"), payload.get("limit")))
            elif route == "/api/rebalance":
                self._json(self.service.rebalance(
                    float(payload.get("threshold", 0.85)),
                    bool(payload.get("apply", False))))
            elif route == "/api/simulate":
                self._json(self.service.simulate())
            elif route == "/api/snapshot":
                self._json(self.service.snapshot(str(payload.get("label", ""))), 201)
            elif route == "/api/restore":
                self._json(self.service.restore(str(payload.get("snapshot_id", ""))))
            elif route.startswith("/api/nodes/") and route.endswith("/drain"):
                node_id = route.split("/")[3]
                self._json(self.service.drain_node(node_id))
            elif route.startswith("/api/nodes/") and route.endswith("/evacuate"):
                node_id = route.split("/")[3]
                self._json(self.service.evacuate(node_id))
            elif route.startswith("/api/nodes/") and route.endswith("/status"):
                node_id = route.split("/")[3]
                self._json(self.service.set_node_status(node_id, str(payload.get("status", ""))))
            elif route.startswith("/api/workloads/") and route.endswith("/complete"):
                workload_id = route.split("/")[3]
                self._json(self.service.complete(
                    workload_id, bool(payload.get("success", True)),
                    str(payload.get("reason", ""))))
            else:
                self._json({"ok": False, "error": f"unknown route {route}"}, 404)
        except Exception as exc:  # noqa: BLE001 - mapped to a status code
            self._error(exc)

    def do_DELETE(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        try:
            if route.startswith("/api/nodes/"):
                node_id = route.split("/", 3)[3]
                self._json(self.service.delete_node(node_id))
            elif route.startswith("/api/workloads/"):
                workload_id = route.split("/", 3)[3]
                self._json(self.service.store.delete_workload(workload_id))
            else:
                self._json({"ok": False, "error": f"unknown route {route}"}, 404)
        except Exception as exc:  # noqa: BLE001
            self._error(exc)

    def log_message(self, *args) -> None:  # quiet by default
        return


def make_server(service: FleetService, host: str = "127.0.0.1",
                port: int = 0) -> tuple[ThreadingHTTPServer, str]:
    server = ThreadingHTTPServer((host, int(port)), _Handler)
    server.service = service  # type: ignore[attr-defined]
    url = f"http://{host}:{server.server_port}"
    return server, url


def serve(service: FleetService, host: str = "127.0.0.1", port: int = 0) -> None:
    server, url = make_server(service, host, port)
    print(url, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def _load_json_flag(value: str | None) -> dict:
    if not value:
        return {}
    text = value
    if value.startswith("@"):
        text = Path(value[1:]).read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except ValueError as exc:
        raise ValidationError(f"--json is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValidationError("--json must contain a JSON object")
    return payload


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _emit(payload) -> None:
    print(json.dumps(payload, indent=2, default=str, sort_keys=True))


def _node_payload(args) -> dict:
    payload = _load_json_flag(getattr(args, "json", None))
    if getattr(args, "node_id", None):
        payload["node_id"] = args.node_id
    if getattr(args, "kind", None):
        payload["kind"] = args.kind
    if getattr(args, "cpu", None) is not None:
        payload["cpu_cores"] = args.cpu
    if getattr(args, "memory", None) is not None:
        payload["memory_gb"] = args.memory
    if getattr(args, "gpus", None) is not None:
        payload["gpu_count"] = args.gpus
    if getattr(args, "region", None):
        payload["region"] = args.region
    if getattr(args, "capabilities", None):
        payload["capabilities"] = _split_csv(args.capabilities)
    if getattr(args, "reliability", None) is not None:
        payload["reliability"] = args.reliability
    if getattr(args, "price", None) is not None:
        payload["price_per_hour"] = args.price
    if getattr(args, "auto_capabilities", False):
        payload["auto_capabilities"] = True
    return payload


def _workload_payload(args) -> dict:
    payload = _load_json_flag(getattr(args, "json", None))
    if getattr(args, "workload_id", None):
        payload["workload_id"] = args.workload_id
    if getattr(args, "name", None):
        payload["name"] = args.name
    if getattr(args, "cpu", None) is not None:
        payload["cpu"] = args.cpu
    if getattr(args, "memory", None) is not None:
        payload["memory_gb"] = args.memory
    if getattr(args, "capabilities", None):
        payload["required_capabilities"] = _split_csv(args.capabilities)
    if getattr(args, "priority", None) is not None:
        payload["priority"] = args.priority
    if getattr(args, "duration", None) is not None:
        payload["duration_s"] = args.duration
    if getattr(args, "deadline", None) is not None:
        payload["deadline_s"] = args.deadline
    if getattr(args, "max_price", None) is not None:
        payload["max_price_per_hour"] = args.max_price
    if getattr(args, "energy_budget", None) is not None:
        payload["energy_budget_wh"] = args.energy_budget
    if getattr(args, "idempotency_key", None):
        payload["idempotency_key"] = args.idempotency_key
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mem20causalroutingbrainz",
        description="Coordinate heterogeneous edge hardware as one capability-aware fleet.")
    parser.add_argument("--store", default=str(default_store_path()),
                        help="SQLite store path (default: %(default)s)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="fleet health, metrics, energy and fault forecast")
    sub.add_parser("metrics", help="raw state-plane counts")
    sub.add_parser("doctor", help="probe every cross-subsystem integration")
    sub.add_parser("simulate", help="replay the six fleet failure scenarios")

    benchmark = sub.add_parser("benchmark", help="measure the placement path")
    benchmark.add_argument("--iterations", type=int, default=20)

    node = sub.add_parser("node", help="node registry")
    node_sub = node.add_subparsers(dest="node_command", required=True)
    node_add = node_sub.add_parser("add", help="register a node")
    node_add.add_argument("--json", default=None, help="full JSON object or @file")
    node_add.add_argument("--id", dest="node_id")
    node_add.add_argument("--kind", choices=[kind.value for kind in DeviceKind])
    node_add.add_argument("--cpu", type=int)
    node_add.add_argument("--memory", type=float)
    node_add.add_argument("--gpus", type=int, help="number of GPUs")
    node_add.add_argument("--region")
    node_add.add_argument("--capabilities", help="comma-separated")
    node_add.add_argument("--reliability", type=float)
    node_add.add_argument("--price", type=float)
    node_add.add_argument("--auto-capabilities", action="store_true")
    node_sub.add_parser("list", help="list nodes")
    node_rm = node_sub.add_parser("delete", help="delete a node")
    node_rm.add_argument("node_id")
    node_status = node_sub.add_parser("status", help="set node status")
    node_status.add_argument("node_id")
    node_status.add_argument("status", choices=[status.value for status in NodeStatus])
    node_drain = node_sub.add_parser("drain", help="drain a node")
    node_drain.add_argument("node_id")
    node_evac = node_sub.add_parser("evacuate", help="evacuate a node")
    node_evac.add_argument("node_id")

    workload = sub.add_parser("workload", help="workload queue")
    workload_sub = workload.add_subparsers(dest="workload_command", required=True)
    workload_add = workload_sub.add_parser("submit", help="submit a workload")
    workload_add.add_argument("--json", default=None, help="full JSON object or @file")
    workload_add.add_argument("--id", dest="workload_id")
    workload_add.add_argument("--name")
    workload_add.add_argument("--cpu", type=float)
    workload_add.add_argument("--memory", type=float)
    workload_add.add_argument("--capabilities", help="comma-separated")
    workload_add.add_argument("--priority", type=int)
    workload_add.add_argument("--duration", type=float)
    workload_add.add_argument("--deadline", type=float)
    workload_add.add_argument("--max-price", type=float)
    workload_add.add_argument("--energy-budget", type=float)
    workload_add.add_argument("--idempotency-key")
    workload_sub.add_parser("list", help="list workloads")
    workload_get = workload_sub.add_parser("get", help="show one workload")
    workload_get.add_argument("workload_id")
    workload_done = workload_sub.add_parser("complete", help="finish a workload")
    workload_done.add_argument("workload_id")
    workload_done.add_argument("--fail", action="store_true")
    workload_done.add_argument("--reason", default="")

    dispatch = sub.add_parser("dispatch", help="place queued workloads")
    dispatch.add_argument("--id", dest="workload_id", default=None)
    dispatch.add_argument("--limit", type=int, default=None)

    rebalance = sub.add_parser("rebalance", help="move work off hot nodes")
    rebalance.add_argument("--threshold", type=float, default=0.85)
    rebalance.add_argument("--apply", action="store_true")

    predict = sub.add_parser("predict", help="fault forecast")
    predict.add_argument("--horizon", type=float, default=3600.0)

    energy = sub.add_parser("energy", help="projected energy draw")
    energy.add_argument("--hours", type=float, default=24.0)

    events = sub.add_parser("events", help="read the event stream")
    events.add_argument("--since", type=int, default=0)
    events.add_argument("--limit", type=int, default=200)

    snapshot = sub.add_parser("snapshot", help="snapshot the fleet")
    snapshot.add_argument("--label", default="")
    restore = sub.add_parser("restore", help="restore a snapshot")
    restore.add_argument("snapshot_id")

    server = sub.add_parser("serve", help="start the HTTP cockpit and JSON API")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8771)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = _service(args)
    try:
        if args.command == "status":
            _emit(service.status())
        elif args.command == "metrics":
            _emit(service.metrics())
        elif args.command == "doctor":
            _emit(service.doctor())
        elif args.command == "simulate":
            _emit(service.simulate())
        elif args.command == "benchmark":
            _emit(service.benchmark(args.iterations))
        elif args.command == "node":
            if args.node_command == "add":
                _emit(service.register_node(_node_payload(args)))
            elif args.node_command == "list":
                _emit({"ok": True, "nodes": service.list_nodes()})
            elif args.node_command == "delete":
                _emit(service.delete_node(args.node_id))
            elif args.node_command == "status":
                _emit(service.set_node_status(args.node_id, args.status))
            elif args.node_command == "drain":
                _emit(service.drain_node(args.node_id))
            elif args.node_command == "evacuate":
                _emit(service.evacuate(args.node_id))
        elif args.command == "workload":
            if args.workload_command == "submit":
                _emit(service.submit_workload(_workload_payload(args)))
            elif args.workload_command == "list":
                _emit({"ok": True, "workloads": service.list_workloads()})
            elif args.workload_command == "get":
                _emit({"ok": True, "workload": service.get_workload(args.workload_id)})
            elif args.workload_command == "complete":
                _emit(service.complete(args.workload_id, not args.fail, args.reason))
        elif args.command == "dispatch":
            _emit(service.dispatch(args.workload_id, args.limit))
        elif args.command == "rebalance":
            _emit(service.rebalance(args.threshold, apply=args.apply))
        elif args.command == "predict":
            _emit({"ok": True, "forecasts": service.predict(args.horizon)})
        elif args.command == "energy":
            _emit({"ok": True, "energy": service.energy(args.hours)})
        elif args.command == "events":
            _emit({"ok": True, "events": service.events(args.since, args.limit)})
        elif args.command == "snapshot":
            _emit(service.snapshot(args.label))
        elif args.command == "restore":
            _emit(service.restore(args.snapshot_id))
        elif args.command == "serve":
            serve(service, args.host, args.port)
        else:  # pragma: no cover - argparse enforces the choices
            parser.error(f"unknown command {args.command}")
            return 2
    except (ValidationError, NotFoundError, ConflictError) as exc:
        _emit({"ok": False, "error": str(exc), "kind": type(exc).__name__})
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
