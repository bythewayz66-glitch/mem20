#!/usr/bin/env python3
"""mem20_mcp CLI - inspect and preflight the canonical MCP tree.

``mem20_mcp`` is a forwarder, so the only questions worth asking about it are
about the tree it forwards to. This CLI answers them without booting a server:

``preflight``
    Run the six admission checks over the canonical tree and print what each
    decided. Exit 1 if the tree would be refused, so it can gate a deploy.

``tools``
    List the tool modules the canonical tree exposes, with the naming class of
    each. A tool that is not an estate address is one no client will address
    correctly.

``root``
    Print the resolved canonical root. This is the one command that does not
    preflight, because its whole purpose is to tell you which tree would be
    checked.

Nothing here writes to the canonical tree.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

from mem20_mcp import _forward, preflight


def cmd_root(args) -> int:
    print(_forward.canonical_root())
    return 0


def cmd_tools(args) -> int:
    root = Path(_forward.canonical_root())
    names = preflight.discover_tool_names(root)
    print(json.dumps(
        {"root": str(root), "count": len(names),
         "tools": {n: preflight.check_tool_name(preflight.exposed_tool_name(n))
                   for n in names}},
        indent=2,
    ))
    return 0


def cmd_preflight(args) -> int:
    # ``canonical_root()`` runs the preflight itself, so a refusal surfaces as
    # ImportError from there rather than from the call below. Both are reported
    # the same way: a refusal is a refusal, whichever layer caught it.
    try:
        root = Path(_forward.canonical_root())
    except ImportError as exc:
        print(json.dumps({"refused": True, "check": "preflight", "reason": str(exc)}, indent=2))
        return 1
    try:
        report = preflight.preflight(
            root,
            intended_uses=args.intended_use,
            at=args.at,
            valid_from=args.valid_from,
            valid_to=args.valid_to,
        )
    except preflight.PreflightRefused as exc:
        print(json.dumps(exc.as_dict(), indent=2))
        return 1
    print(json.dumps({"admitted": True, "report": report.as_dict()}, indent=2))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="mem20_mcp", description="mem20_mcp forwarder CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("root", help="print the resolved canonical root")
    p.set_defaults(func=cmd_root)

    p = sub.add_parser("tools", help="list canonical tool modules and their naming class")
    p.set_defaults(func=cmd_tools)

    p = sub.add_parser("preflight", help="run the admission checks over the canonical tree")
    p.add_argument("--intended-use", action="append", default=None,
                   help="declare what this tree is being exposed for")
    p.add_argument("--at", default=None, help="ISO-8601 instant to check against the release window")
    p.add_argument("--valid-from", default=None)
    p.add_argument("--valid-to", default=None)
    p.set_defaults(func=cmd_preflight)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
