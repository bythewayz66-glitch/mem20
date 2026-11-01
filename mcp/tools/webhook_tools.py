"""MCP tools for the webhook supernetwork (mem20webhooksupernetworkz).

Registration here is genuinely two-part, which is the point:

* ``TOOLS`` is the declarative list an MCP server reads to expose the tools.
* ``install(server)`` performs the actual registration on a live server object.

A tools module that is imported by nobody - or listed in a registry file whose
value is never dispatched - changes nothing. That is why ``mcp/server.py`` calls
``register_webhook_tools()`` from its constructor and binds each handler as
``_<tool_name>``, matching the dispatcher's naming convention, and why
``tests/test_estate_wiring.py`` builds a server object and drives a real call
through it.

Every handler goes through the subsystem's real receiver, so a tool call
exercises the same estate wiring and the same refusals the CLI and the tests do.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

__all__ = ["TOOLS", "install", "handle"]

# <repo>/mcp/tools/webhook_tools.py -> <repo>
_REPO_ROOT = Path(__file__).resolve().parents[2]
_PKG = _REPO_ROOT / "mem20webhooksupernetworkz"
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))


def _receiver(tolerance_seconds: float = 300.0, secret: str | None = None):
    """Build a receiver from the environment.

    The secret is read from ``MEM20_WEBHOOK_SECRET`` and never defaulted: a
    receiver with an empty HMAC key would accept a signature computed over an
    empty key, which is worse than refusing to run.
    """
    from mem20webhooksupernetworkz.domain import WebhookSuperNetwork

    key = secret or os.environ.get("MEM20_WEBHOOK_SECRET")
    if not key:
        raise ValueError(
            "MEM20_WEBHOOK_SECRET is not set. A receiver with no HMAC key would "
            "accept signatures forged over an empty key, so it refuses to start.")
    return WebhookSuperNetwork(key, tolerance_seconds=float(tolerance_seconds))


def webhook_verify(body: str, timestamp: float, signature: str,
                   payload: str | None = None, now: float | None = None,
                   tolerance_seconds: float = 300.0,
                   secret: str | None = None) -> dict:
    """Verify a delivery: freshness, signature, event time and payload class."""
    import json

    receiver = _receiver(tolerance_seconds, secret)
    report: dict = {"signature_ok": False, "event_time": None, "admission": None}
    try:
        receiver.verify(body, timestamp, signature, now=now)
    except Exception as exc:  # noqa: BLE001 - the verdict is the payload
        report["signature_ok"] = False
        report["error"] = f"{type(exc).__name__}: {exc}"
        return report
    report["signature_ok"] = True
    report["event_time"] = receiver.verify_event_time(timestamp, now=now)
    if payload:
        verdict = receiver.admit(json.loads(payload))
        report["admission"] = {"safe": verdict["safe"],
                               "severity": verdict["severity"],
                               "kind": verdict["kind"],
                               "field": verdict["field"]}
    return report


def webhook_deliver(body: str, timestamp: float, signature: str,
                    idempotency_key: str | None = None,
                    payload: str | None = None,
                    tolerance_seconds: float = 300.0,
                    secret: str | None = None) -> dict:
    """Deliver once per idempotency key. A repeat is skipped, not re-sent."""
    import json

    receiver = _receiver(tolerance_seconds, secret)
    try:
        return receiver.deliver(
            body, timestamp, signature, idempotency_key=idempotency_key,
            payload=json.loads(payload) if payload else None)
    except Exception as exc:  # noqa: BLE001
        # A refusal is an outcome, not a crash: report it as data so a client
        # can distinguish "rejected on purpose" from "the tool broke".
        return {"delivered": False, "refused": type(exc).__name__,
                "error": str(exc)}


def webhook_replay(events_path: str, verify_store: bool = True,
                   secret: str | None = None) -> dict:
    """Re-deliver a stored event log, after verifying the store it came from."""
    import json

    receiver = _receiver(secret=secret)
    with open(events_path, encoding="utf-8") as handle:
        events = [json.loads(line) for line in handle if line.strip()]
    try:
        return receiver.replay(events, verify_store=verify_store)
    except ValueError as exc:
        return {"replayed": 0, "refused": "store", "error": str(exc)}


def webhook_route_capabilities(limit: int = 5) -> dict:
    """Which capabilities the estate exposes, from toolchest's own catalog."""
    return _receiver(secret="unused-for-reads").route_capabilities(limit)


def webhook_doctor() -> dict:
    """Probe every estate project this receiver is wired to."""
    from mem20webhooksupernetworkz import estate

    checks: dict[str, dict] = {}

    def probe(name: str, fn) -> None:
        try:
            checks[name] = {"ok": True, "result": fn()}
        except Exception as exc:  # noqa: BLE001 - the report is the point
            checks[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    probe("mem20secretz.sweep.classify",
          lambda: estate.classify_payload({"deploy": "staging"})["safe"])
    probe("mem20liez.gates.check_prohibited_uses",
          lambda: estate.check_route_legality(["webhook_routing"])["permitted"])
    probe("mem20verify.dataintegrity.check",
          lambda: estate.verify_store()["ok"])
    probe("mem20ops.memchecks.identity_check",
          lambda: "store_path" in estate.identity())
    probe("memory_engine.validate_event_time",
          lambda: estate.validate_event_time(1772323200.0))
    probe("toolchest.catalog.load_inventory",
          lambda: estate.tool_inventory()["total"])

    wired = sum(1 for c in checks.values() if c["ok"])
    return {"checks": checks, "wired": wired, "total": len(checks),
            "ok": wired == len(checks)}


TOOLS = [
    {
        "name": "webhook_verify",
        "description": "Verify a webhook delivery's freshness, HMAC signature, "
                       "event time and payload credential class. Returns the "
                       "estate's verdicts rather than raising.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "body": {"type": "string"},
                "timestamp": {"type": "number"},
                "signature": {"type": "string"},
                "payload": {"type": "string",
                            "description": "JSON body, to check credential class"},
                "now": {"type": "number"},
                "tolerance_seconds": {"type": "number", "default": 300},
            },
            "required": ["body", "timestamp", "signature"],
        },
        "handler": webhook_verify,
    },
    {
        "name": "webhook_deliver",
        "description": "Verify, admit and deliver a webhook event once per "
                       "idempotency key. A duplicate is skipped, and a payload "
                       "carrying a credential is refused.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "body": {"type": "string"},
                "timestamp": {"type": "number"},
                "signature": {"type": "string"},
                "idempotency_key": {"type": "string"},
                "payload": {"type": "string"},
                "tolerance_seconds": {"type": "number", "default": 300},
            },
            "required": ["body", "timestamp", "signature"],
        },
        "handler": webhook_deliver,
    },
    {
        "name": "webhook_replay",
        "description": "Re-deliver a JSONL event log, refusing when "
                       "mem20verify reports the store cannot round-trip.",
        "inputSchema": {
            "type": "object",
            "properties": {"events_path": {"type": "string"},
                           "verify_store": {"type": "boolean", "default": True}},
            "required": ["events_path"],
        },
        "handler": webhook_replay,
    },
    {
        "name": "webhook_route_capabilities",
        "description": "List the capabilities a route may target, read from "
                       "toolchest's catalog.",
        "inputSchema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 5}},
        },
        "handler": webhook_route_capabilities,
    },
    {
        "name": "webhook_doctor",
        "description": "Probe the six estate projects the receiver is wired to.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": webhook_doctor,
    },
]

_BY_NAME = {tool["name"]: tool["handler"] for tool in TOOLS}


def handle(name: str, arguments: dict | None = None) -> dict:
    """Dispatch a tool call by name. Raises KeyError for an unknown tool."""
    return _BY_NAME[name](**(arguments or {}))


def install(server) -> list[str]:
    """Register every tool on a live MCP server object.

    Accepts either a ``register``-style method or a plain ``tools`` dict, since
    the estate's servers use both. Returns the names registered so the caller -
    and a test - can assert the tools actually reached the server instead of
    trusting that the import happened.
    """
    registered: list[str] = []
    for tool in TOOLS:
        if hasattr(server, "register"):
            server.register(tool["name"], tool["description"],
                            tool["inputSchema"], tool["handler"])
        elif isinstance(getattr(server, "tools", None), dict):
            server.tools[tool["name"]] = {
                "name": tool["name"], "description": tool["description"],
                "inputSchema": tool["inputSchema"], "handler": tool["handler"],
            }
        else:  # pragma: no cover - server contract changed
            raise TypeError(
                f"cannot register MCP tools on {type(server).__name__}: it has "
                f"neither register() nor a tools dict")
        registered.append(tool["name"])
    return registered
