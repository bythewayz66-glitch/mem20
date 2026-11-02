#!/usr/bin/env python3
"""mem20_mcp CLI - inspect, preflight and audit the canonical MCP tree.

``mem20_mcp`` is a forwarder, so the only questions worth asking about it are
about the tree it forwards to, and about whether the forwarding is still real.
This CLI answers both without booting a server:

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

``audit``
    Audit the forwarding shims themselves: does each one still forward, or has
    it quietly grown its own implementation? Exit 1 if any shim has drifted.

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
from mem20_mcp.loader_audit import AuditRefused, run_audit


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


def _print_audit(audit) -> None:
    verdict = "CLEAN" if audit.clean else "BROKEN"
    print(f"mem20_mcp loader audit: {verdict}")
    print(f"root: {audit.root}")
    print(f"shims: {len(audit.shims)}  broken: {len(audit.broken)}")
    print()
    width = max((len(s.module) for s in audit.shims), default=8)
    print(f"package naming: {audit.naming}")
    print()
    print(f"{'module':<{width}}  {'forwards':8}  {'via':22}  stubs  result")
    for s in audit.shims:
        mark = "ok" if s.ok else "FAIL"
        print(
            f"{s.module:<{width}}  {str(s.forwards):8}  {s.via or '-':22}  "
            f"{s.stub_issues:>5}  {mark}"
        )
    if audit.broken:
        print("\nproblems:")
        for s in audit.broken:
            for p in s.problems:
                print(f"  - {s.module}: {p}")
    print()
    print(
        f"log noise: kept {audit.wire_kept}, swallowed {audit.wire_swallowed}, "
        f"waste {audit.wire_waste_ratio:.2%}"
    )
    prov = audit.provenance or {}
    if prov:
        if prov.get("committed"):
            print(f"provenance: committed cid={prov.get('cid')}")
        else:
            print(f"provenance: NOT committed ({prov.get('reason')})")


def cmd_audit(args) -> int:
    try:
        audit = run_audit(
            args.root,
            intended_uses=args.intended_use,
            valid_from=args.valid_from,
            valid_to=args.valid_to,
            at=args.at,
        )
    except AuditRefused as exc:
        if args.json:
            print(json.dumps(exc.as_dict(), indent=2))
        else:
            print(f"refused: {exc.check}: {exc.reason}")
        return 2
    if args.json:
        print(json.dumps(audit.as_dict(), indent=2, default=str))
    else:
        _print_audit(audit)
    return 0 if audit.clean else 1


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

    p = sub.add_parser("audit", help="audit the forwarding shims for drift")
    p.add_argument("--root", default=None, help="package root to audit")
    p.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    p.add_argument("--intended-use", action="append", default=None,
                   help="declare what this audit is for; checked against the prohibited-use list")
    p.add_argument("--at", default=None, help="ISO-8601 instant for the audit window")
    p.add_argument("--valid-from", default=None)
    p.add_argument("--valid-to", default=None)
    p.set_defaults(func=cmd_audit)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
