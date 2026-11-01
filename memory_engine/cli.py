"""Command-line surface for memory_engine.

Every subcommand emits the shared ``mem20.cli/1`` JSON envelope when ``--json``
is passed, so a fleet script can parse memory_engine output the same way it
parses every other subsystem's.

Subcommands:

* ``stats``    -- what the store currently holds
* ``recall``   -- read facts back by topic / tag
* ``remember`` -- write a grounded fact (epistemic status is required)
* ``wiring``   -- prove the cross-subsystem edges, exit non-zero if any is dead
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from memory_engine import integrations, memory


def _emit(payload: Dict[str, Any], as_json: bool, command: str, argv: List[str],
          exit_code: int = 0) -> int:
    """Print either the shared envelope or a human summary."""
    if as_json:
        envelope = integrations.cli_envelope(
            command, argv, exit_code,
            stdout=json.dumps(payload, default=str),
        )
        print(json.dumps(envelope, indent=1, default=str))
    else:
        print(json.dumps(payload, indent=1, default=str))
    return exit_code


def cmd_stats(args: argparse.Namespace) -> int:
    from pathlib import Path

    ledger = memory.LEDGER
    entries_dir = Path(memory.ENTRIES)
    entry_files = sorted(entries_dir.glob("*.md")) if entries_dir.is_dir() else []
    payload = {
        "store_dir": memory.STORE_DIR,
        "ledger": ledger,
        "ledger_exists": Path(ledger).is_file(),
        "entry_files": len(entry_files),
        "vector_available": bool(getattr(memory, "VECTOR_AVAILABLE", False)),
        "bm25_available": bool(getattr(memory, "BM25_AVAILABLE", False)),
    }
    return _emit(payload, args.json, "stats", args.argv)


def cmd_recall(args: argparse.Namespace) -> int:
    text = memory.recall(topic=args.topic, tags=args.tag or None)
    payload = {"topic": args.topic, "tags": args.tag, "result": text}
    return _emit(payload, args.json, "recall", args.argv)


def cmd_remember(args: argparse.Namespace) -> int:
    try:
        rec = memory.remember(
            topic=args.topic,
            content=args.content,
            tags=args.tag or [],
            epistemic_status=args.epistemic_status,
            source=args.source,
        )
    except (ValueError, PermissionError) as exc:
        # A refused write is a real outcome, not a crash: report it in the
        # envelope with a non-zero exit so a script can branch on it.
        return _emit({"error": f"{type(exc).__name__}: {exc}"}, args.json,
                     "remember", args.argv, exit_code=2)
    return _emit({"recorded": rec}, args.json, "remember", args.argv)


def cmd_wiring(args: argparse.Namespace) -> int:
    report = integrations.wiring_report(record=args.record)
    return _emit(report, args.json, "wiring", args.argv,
                 exit_code=0 if report["ok"] else 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="memory_engine",
        description="Grounded memory store: read, write and audit facts.",
    )
    # --json is accepted both before and after the subcommand: fleet scripts
    # write `memory_engine stats --json`, and a global-only flag would reject
    # that. SUPPRESS keeps the subparser copy from clobbering the global one.
    parser.add_argument("--json", action="store_true",
                        help="emit the shared mem20.cli/1 JSON envelope")
    sub = parser.add_subparsers(dest="command", required=True)

    def _add_json(p):
        p.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                       help="emit the shared mem20.cli/1 JSON envelope")
        return p

    p_stats = _add_json(sub.add_parser("stats", help="what the store currently holds"))
    p_stats.set_defaults(func=cmd_stats)

    p_recall = _add_json(sub.add_parser("recall", help="read facts back"))
    p_recall.add_argument("--topic")
    p_recall.add_argument("--tag", action="append")
    p_recall.set_defaults(func=cmd_recall)

    p_remember = _add_json(sub.add_parser("remember", help="write a grounded fact"))
    p_remember.add_argument("--topic", required=True)
    p_remember.add_argument("--content", required=True)
    p_remember.add_argument("--tag", action="append")
    p_remember.add_argument("--epistemic-status", required=True,
                            help="how this was learned; 'unlabeled' if unknown")
    p_remember.add_argument("--source")
    p_remember.set_defaults(func=cmd_remember)

    p_wiring = _add_json(sub.add_parser("wiring", help="prove the cross-subsystem edges"))
    p_wiring.add_argument("--record", action="store_true",
                          help="also write the estate snapshot as a grounded fact")
    p_wiring.set_defaults(func=cmd_wiring)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    # The envelope echoes the argv it was given, minus the --json flag itself.
    args.argv = [a for a in argv if a != "--json"]
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
