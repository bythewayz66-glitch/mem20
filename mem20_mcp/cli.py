"""CLI for the mem20_mcp loader-integrity audit.

    python3 -m mem20_mcp.cli audit
    python3 -m mem20_mcp.cli audit --json
    python3 -m mem20_mcp.cli audit --root /opt/mem20/mcp

Exit code 0 only when every shim forwards, is named like an estate module, and
has a real body. A broken shim is reported per module, never silently skipped.
"""

from __future__ import annotations

import argparse
import json
import sys

from .loader_audit import AuditRefused, run_audit


def _print_human(audit) -> None:
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="mem20_mcp",
        description="mem20_mcp loader-integrity audit",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("audit", help="audit every forwarding shim in the package")
    p.add_argument("--root", default=None, help="package root to audit")
    p.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    p.add_argument(
        "--intended-use",
        action="append",
        default=[],
        help="declare what this audit is for; checked against the prohibited-use list",
    )
    p.add_argument("--at", default=None, help="ISO-8601 instant for the audit window")
    p.add_argument("--valid-from", default=None)
    p.add_argument("--valid-to", default=None)

    args = ap.parse_args(argv)

    if args.cmd == "audit":
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
            _print_human(audit)
        return 0 if audit.clean else 1

    return 2


if __name__ == "__main__":
    sys.exit(main())
