#!/usr/bin/env python3
"""CLI for the mem20 MCP tool surface.

Three verbs, all read-only:

    admit <tool> [--source FILE] [--use TEXT ...] [--at ISO]
        Run every admission check for one tool and print the verdict.
    audit [--at ISO]
        Admit every tool in the live registry and print the summary.
    registry
        Print the registered tool names, one per line.

Exit codes: 0 admitted / clean, 1 refused / refusals found, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:  # imported as a package (python -m mcp.cli)
    from .surface import admit_tool, audit_registry
except ImportError:  # run as a script (python mcp/cli.py); the repo's mcp/ dir is on sys.path
    from surface import admit_tool, audit_registry


def _load_registry():
    """Import the server and build its registry.

    Imported lazily: ``server`` pulls the MCP SDK and every tool mixin, which is
    far more than ``admit`` on a source file needs.
    """
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    import server  # noqa: PLC0415 - deliberately deferred

    return server.Mem20MCPServer().tools


def _cmd_admit(args: argparse.Namespace) -> int:
    source = None
    path = "<tool>"
    if args.source:
        path = args.source
        source = Path(args.source).read_text(encoding="utf-8")
    admission = admit_tool(
        args.tool,
        source=source,
        path=path,
        intended_uses=args.use,
        valid_from=args.valid_from,
        valid_to=args.valid_to,
        at=args.at,
    )
    if args.json:
        print(json.dumps({
            "tool": admission.tool,
            "admitted": admission.admitted,
            "checks": [{"name": c.name, "ok": c.ok, "reason": c.reason}
                       for c in admission.checks],
        }, indent=2))
    else:
        print(admission.explain())
    return 0 if admission.admitted else 1


def _cmd_audit(args: argparse.Namespace) -> int:
    summary = audit_registry(_load_registry(), at=args.at)
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"tools: {summary['total']}  admitted: {summary['admitted']}  "
              f"refused: {summary['refused']}")
        for refusal in summary["refusals"]:
            print(f"  - {refusal['tool']}: {'; '.join(refusal['reasons'])}")
    return 0 if summary["refused"] == 0 else 1


def _cmd_registry(args: argparse.Namespace) -> int:
    tools = _load_registry()
    if args.json:
        print(json.dumps(sorted(tools), indent=2))
    else:
        for name in sorted(tools):
            print(name)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mem20-mcp-surface",
        description="Admission control for the mem20 MCP tool surface.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    admit = sub.add_parser("admit", help="run every admission check for one tool")
    admit.add_argument("tool", help="tool name, e.g. memory_store")
    admit.add_argument("--source", help="handler source file to lint for stubs")
    admit.add_argument("--use", action="append", default=None,
                       help="declared intended use (repeatable)")
    admit.add_argument("--valid-from", default=None, help="ISO start of validity window")
    admit.add_argument("--valid-to", default=None, help="ISO end of validity window")
    admit.add_argument("--at", default=None, help="ISO instant to test the window against")
    admit.add_argument("--json", action="store_true", help="machine-readable output")
    admit.set_defaults(func=_cmd_admit)

    audit = sub.add_parser("audit", help="admit every tool in the live registry")
    audit.add_argument("--at", default=None, help="ISO instant for temporal checks")
    audit.add_argument("--json", action="store_true", help="machine-readable output")
    audit.set_defaults(func=_cmd_audit)

    registry = sub.add_parser("registry", help="list registered tool names")
    registry.add_argument("--json", action="store_true", help="machine-readable output")
    registry.set_defaults(func=_cmd_registry)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
