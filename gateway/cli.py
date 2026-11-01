#!/usr/bin/env python3
"""mem20 gateway CLI.

The relay's argument parsing lives in ``hermes_gateway.parse_args`` and its
behaviour in ``hermes_gateway.main``; this module is the named entry point the
estate's tooling looks for, and it adds the two commands that are about the
relay's *policy* rather than its traffic:

``admission``
    Run the six admission checks against a hypothetical message and print what
    each one decided, without writing anything. This is how you find out why a
    message would be refused before you send it.

``audit``
    Run the stub linter over the gateway's own source. A relay whose handler
    body is ``pass`` returns a well-formed entry that was never written, and the
    sender cannot tell.

Both are read-only. Neither writes to ``messages.jsonl``.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import hermes_gateway
import relay


def cmd_admission(args) -> int:
    """Dry-run the admission checks for one message. Writes nothing."""
    try:
        admission, kept = relay.admit(
            args.agent_name,
            args.kind,
            hermes_gateway.GATEWAY_DIR,
            intended_uses=args.intended_use,
            wire=[{"command": c, "text": t} for c, t in (args.wire or [])],
            at=args.at,
        )
    except relay.RelayRefused as exc:
        print(json.dumps(exc.as_dict(), indent=2))
        return 1
    print(json.dumps(
        {"admitted": True, "admission": admission.as_dict(),
         "wire_kept": [line.text for line in kept]},
        indent=2,
    ))
    return 0


def cmd_audit(args) -> int:
    """Run the stub linter over the gateway's own source."""
    issues = relay.audit_gateway_source(HERE)
    if not issues:
        print(json.dumps({"stub_issues": 0, "clean": True}, indent=2))
        return 0
    print(json.dumps(
        {"stub_issues": len(issues),
         "issues": [f"{i.path}:{i.line}:{i.check}" for i in issues]},
        indent=2,
    ))
    return 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # The relay's own commands (register/list/broadcast/read) are handled by
    # hermes_gateway; only the two policy commands are ours.
    if argv and argv[0] in {"admission", "audit"}:
        ap = argparse.ArgumentParser(prog="gateway-cli")
        sub = ap.add_subparsers(dest="cmd", required=True)

        p = sub.add_parser("admission", help="dry-run the admission checks; writes nothing")
        p.add_argument("agent_name", help="agent name to check")
        p.add_argument("--kind", default="broadcast")
        p.add_argument("--intended-use", action="append", default=None)
        p.add_argument("--at", default=None, help="ISO-8601 instant to check against the window")
        p.add_argument("--wire", action="append", nargs=2, metavar=("COMMAND", "TEXT"),
                       default=None, help="a transport line to filter, e.g. --wire 372 '- motd'")
        p.set_defaults(func=cmd_admission)

        p = sub.add_parser("audit", help="run the stub linter over the gateway source")
        p.set_defaults(func=cmd_audit)

        args = ap.parse_args(argv)
        return args.func(args)

    return hermes_gateway.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
