"""Command line for the webhook supernetwork.

    init     create a receiver (checks admissibility and names its store)
    sign     sign a body+timestamp the way a provider would
    verify   verify a delivery: signature, freshness, event time, payload class
    deliver  verify, admit and deliver once per idempotency key
    replay   re-deliver stored events, after verifying the store
    doctor   probe every estate project this receiver is wired to
    selftest prove the receiver's claims on a throwaway ledger

Output is JSON so it composes; refusals go to stderr with a non-zero exit.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time

from .domain import DeliveryLedger, PayloadRefusedError, WebhookSuperNetwork, \
    WebhookVerificationError

DEFAULT_LEDGER = os.environ.get(
    "MEM20_WEBHOOK_LEDGER", os.path.expanduser("~/.mem20/webhook/delivered.txt"))


def _emit(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


def _receiver(args) -> WebhookSuperNetwork:
    uses = [u.strip() for u in (args.intended_uses or "").split(",") if u.strip()]
    return WebhookSuperNetwork(
        args.secret,
        tolerance_seconds=args.tolerance,
        intended_uses=uses or None,
        ledger_path=args.ledger,
    )


def cmd_init(args, _none=None):
    """Show what the receiver would be, without delivering anything."""
    receiver = _receiver(args)
    _emit({
        "tolerance_seconds": receiver.tolerance,
        "legality": receiver.legality,
        "store_identity": receiver.store_identity(),
        "route_capabilities": receiver.route_capabilities(limit=3),
        "ledger": {"path": args.ledger, "remembered": len(receiver.delivered)},
    })
    return 0


def cmd_sign(args, _none=None):
    receiver = _receiver(args)
    _emit({"signature": receiver.sign(args.body, args.timestamp),
           "timestamp": args.timestamp, "body": args.body})
    return 0


def cmd_verify(args, _none=None):
    """Signature, freshness, event time and - with ``--payload`` - class."""
    receiver = _receiver(args)
    payload = json.loads(args.payload) if args.payload else None
    headers = tuple(h.strip() for h in (args.headers or "").split(",") if h.strip())
    report = {
        "signature_ok": False,
        "event_time": None,
        "admission": None,
    }
    try:
        receiver.verify(args.body, args.timestamp, args.signature, now=args.now)
        report["signature_ok"] = True
    except WebhookVerificationError as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        _emit(report)
        return 2
    report["event_time"] = receiver.verify_event_time(args.timestamp, now=args.now)
    if payload is not None:
        try:
            report["admission"] = receiver.admit(payload, headers)
        except PayloadRefusedError as exc:
            report["admission"] = {"safe": False, "error": str(exc)}
            _emit(report)
            return 3
    _emit(report)
    return 0


def cmd_deliver(args, _none=None):
    receiver = _receiver(args)
    payload = json.loads(args.payload) if args.payload else None
    headers = tuple(h.strip() for h in (args.headers or "").split(",") if h.strip())
    try:
        outcome = receiver.deliver(
            args.body, args.timestamp, args.signature, now=args.now,
            idempotency_key=args.idem, payload=payload, header_names=headers)
    except PayloadRefusedError as exc:
        _emit({"delivered": False, "refused": "payload", "error": str(exc)})
        return 3
    except WebhookVerificationError as exc:
        _emit({"delivered": False, "refused": "verification", "error": str(exc)})
        return 2
    _emit(outcome)
    return 0


def cmd_replay(args, _none=None):
    receiver = _receiver(args)
    with open(args.events, encoding="utf-8") as handle:
        events = [json.loads(line) for line in handle if line.strip()]
    try:
        report = receiver.replay(events, verify_store=not args.no_verify)
    except ValueError as exc:
        _emit({"replayed": 0, "error": str(exc)})
        return 4
    _emit(report)
    return 0


def cmd_doctor(args, _none=None):
    """Exercise each estate project, naming any gap instead of one traceback."""
    from . import estate

    checks: dict[str, dict] = {}

    def probe(name: str, fn) -> None:
        try:
            checks[name] = {"ok": True, "result": fn()}
        except Exception as exc:  # noqa: BLE001 - the report is the point
            checks[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    probe("mem20secretz.sweep.classify",
          lambda: estate.classify_payload({"deploy": "staging"}))
    probe("mem20liez.gates.check_prohibited_uses",
          lambda: estate.check_route_legality(["webhook_routing"]))
    probe("mem20verify.dataintegrity.check",
          lambda: {k: v for k, v in estate.verify_store().items()
                   if k in ("ok", "checked", "roundtrip_ok", "error")})
    probe("mem20ops.memchecks.identity_check",
          lambda: {k: v for k, v in estate.identity().items()
                   if k in ("store_path", "pinned_block_count", "namespace_count")})
    probe("memory_engine.validate_event_time",
          lambda: estate.validate_event_time(time.time()))
    probe("toolchest.catalog.load_inventory",
          lambda: {k: estate.tool_inventory()[k] for k in ("total", "source")})

    wired = sum(1 for c in checks.values() if c["ok"])
    _emit({"estate": estate.estate_status(), "checks": checks,
           "wired": wired, "total": len(checks), "ok": wired == len(checks)})
    return 0 if wired == len(checks) else 1


def cmd_selftest(args, _none=None):
    """Prove the receiver's claims on a throwaway ledger. Touches nothing real."""
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as tmp:
        ledger = os.path.join(tmp, "delivered.txt")
        ts = 1_772_323_200.0          # 2026-03-01T00:00:00Z
        receiver = WebhookSuperNetwork("s3cret", tolerance_seconds=60,
                                       ledger_path=ledger)
        body = '{"deploy":"staging","sha":"abc123"}'
        sig = receiver.sign(body, ts)

        checks.append(("a valid signature verifies",
                       receiver.verify(body, ts, sig, now=ts) is True))

        try:
            receiver.verify("TAMPERED", ts, sig, now=ts)
            checks.append(("a tampered body is refused", False))
        except WebhookVerificationError as exc:
            checks.append(("a tampered body is refused", "mismatch" in str(exc)))

        try:
            receiver.verify(body, ts, sig, now=ts + 600)
            checks.append(("a stale replay is refused", False))
        except WebhookVerificationError as exc:
            checks.append(("a stale replay is refused", "stale" in str(exc)))

        first = receiver.deliver(body, ts, sig, now=ts, idempotency_key="k1",
                                 payload=json.loads(body))
        checks.append(("a first delivery goes through",
                       first["delivered"] is True))
        second = receiver.deliver(body, ts, sig, now=ts, idempotency_key="k1",
                                  payload=json.loads(body))
        checks.append(("a duplicate is skipped, not re-delivered",
                       second["delivered"] is False
                       and second["reason"] == "duplicate"))

        # The ledger survives a process restart: this is the defect the file
        # exists for.
        reopened = WebhookSuperNetwork("s3cret", tolerance_seconds=60,
                                       ledger_path=ledger)
        checks.append(("delivered keys survive a restart",
                       "k1" in reopened.delivered))

        try:
            receiver.admit({"api_token": "ghp_abc123def456ghi789jkl012mno345"})
            checks.append(("a credential payload is refused", False))
        except PayloadRefusedError:
            checks.append(("a credential payload is refused", True))

        checks.append(("event time is normalised by the ledger's validator",
                       receiver.verify_event_time(ts) ==
                       "2026-03-01T00:00:00+00:00"))

        report = receiver.replay([
            {"body": body, "timestamp": ts, "signature": sig, "now": ts,
             "idempotency_key": "k1"},
            {"body": body, "timestamp": ts, "signature": sig, "now": ts,
             "idempotency_key": "k2"},
        ])
        checks.append(("replay skips what was already delivered",
                       report["replayed"] == 1 and report["skipped"] == 1))

        bounded = DeliveryLedger(max_entries=2)
        for key in ("a", "b", "c"):
            bounded.add(key)
        checks.append(("the ledger is bounded, not unbounded",
                       len(bounded) == 2 and "a" not in bounded))

    failed = [name for name, ok in checks if not ok]
    _emit({"checks": len(checks), "passed": len(checks) - len(failed),
           "failed": failed, "ok": not failed,
           "results": [{"check": name, "ok": ok} for name, ok in checks]})
    return 1 if failed else 0


HANDLERS = {
    "init": cmd_init, "sign": cmd_sign, "verify": cmd_verify,
    "deliver": cmd_deliver, "replay": cmd_replay, "doctor": cmd_doctor,
    "selftest": cmd_selftest,
}


_COMMON_DEFAULTS = {
    "secret": os.environ.get("MEM20_WEBHOOK_SECRET"),
    "tolerance": 300.0,
    "intended_uses": "",
    "ledger": DEFAULT_LEDGER,
    "now": None,
}


def _add_common(parser: argparse.ArgumentParser, *, suppress: bool,
                help_text: bool) -> None:
    """Add the shared options.

    ``suppress`` is what makes ``--secret X doctor`` and ``doctor --secret X``
    both work. argparse normally gives every subparser its own default for each
    option, and the subparser's default overwrites the value the parent parser
    already parsed - so a global flag silently vanished whenever it came before
    the subcommand. ``SUPPRESS`` means "do not set an attribute at all when the
    flag is absent", so the parent's value survives.
    """
    def default(value):
        return argparse.SUPPRESS if suppress else value

    def helptext(text: str) -> str | None:
        return text if help_text else argparse.SUPPRESS

    parser.add_argument("--secret", default=default(_COMMON_DEFAULTS["secret"]),
                        help=helptext("shared HMAC secret (or MEM20_WEBHOOK_SECRET)"))
    parser.add_argument("--tolerance", type=float,
                        default=default(_COMMON_DEFAULTS["tolerance"]),
                        help=helptext("replay window in seconds (default 300)"))
    parser.add_argument("--intended-uses", dest="intended_uses",
                        default=default(_COMMON_DEFAULTS["intended_uses"]),
                        help=helptext("comma-separated declared uses, checked by mem20liez"))
    parser.add_argument("--ledger", default=default(_COMMON_DEFAULTS["ledger"]),
                        help=helptext(f"delivery ledger file (default {DEFAULT_LEDGER})"))
    parser.add_argument("--now", type=float, default=default(_COMMON_DEFAULTS["now"]),
                        help=helptext("override the wall clock (testing)"))


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    _add_common(common, suppress=True, help_text=False)

    parser = argparse.ArgumentParser(
        prog="mem20webhooksupernetworkz",
        description="Signed, deduplicated, replay-resistant webhook delivery.")
    # The same options on the parent, so they may precede the subcommand.
    _add_common(parser, suppress=False, help_text=True)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", parents=[common],
                   help="show the receiver's admissibility and store identity")

    p = sub.add_parser("sign", parents=[common], help="sign a body")
    p.add_argument("body")
    p.add_argument("--timestamp", type=float, required=True)

    p = sub.add_parser("verify", parents=[common],
                       help="verify signature, freshness, event time and payload class")
    p.add_argument("body")
    p.add_argument("--timestamp", type=float, required=True)
    p.add_argument("--signature", required=True)
    p.add_argument("--payload", help="JSON body, to check credential class")
    p.add_argument("--headers", help="comma-separated header names to classify")

    p = sub.add_parser("deliver", parents=[common],
                       help="verify, admit and deliver once per key")
    p.add_argument("body")
    p.add_argument("--timestamp", type=float, required=True)
    p.add_argument("--signature", required=True)
    p.add_argument("--payload", help="JSON body, to check credential class")
    p.add_argument("--headers", help="comma-separated header names to classify")
    p.add_argument("--idem", help="idempotency key")

    p = sub.add_parser("replay", parents=[common],
                       help="re-deliver stored events after verifying the store")
    p.add_argument("events", help="JSONL file of events")
    p.add_argument("--no-verify", dest="no_verify", action="store_true",
                   help="skip the mem20verify round-trip check (inspection only)")

    sub.add_parser("doctor", parents=[common],
                   help="probe every estate project this receiver uses")
    sub.add_parser("selftest", parents=[common],
                   help="prove the receiver's claims on a throwaway ledger")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "selftest" and not args.secret:
        print(json.dumps({"error": "NoSecret",
                          "message": "pass --secret or set MEM20_WEBHOOK_SECRET"}),
              file=sys.stderr)
        return 2
    try:
        return HANDLERS[args.command](args) or 0
    except (WebhookVerificationError, PayloadRefusedError) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}),
              file=sys.stderr)
        return 2
    except ValueError as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
