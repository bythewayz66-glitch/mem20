"""memory_engine CLI — the agent-facing entry point for the 4.0 substrate.

Every subcommand does real work and prints real numbers, or says plainly that it
cannot and why. Nothing here is simulated.

    python -m memory_engine status
    python -m memory_engine remember --topic t --content "..." --epistemic-status observed
    python -m memory_engine recall --topic t
    python -m memory_engine veto --id <fact-id>
    python -m memory_engine guard --id <fact-id>
    python -m memory_engine namespace --agent "my agent"
    python -m memory_engine subsystem --name mem20kilnz
    python -m memory_engine health

Add ``--json`` to any subcommand for the fleet envelope (mem20cliz schema).
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Optional

from . import substrate as S


def _emit(payload: Any, *, as_json: bool, command: str, argv: list[str]) -> int:
    """Print a result, either human-readable or as the fleet JSON envelope."""
    if as_json:
        text = json.dumps(payload, indent=2, sort_keys=True, default=str)
        env = S.envelope(command, argv, 0, text, "")
        print(json.dumps(env, indent=2, sort_keys=True, default=str))
        return 0
    if isinstance(payload, str):
        print(payload)
    else:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0


def _fail(message: str, *, as_json: bool, command: str, argv: list[str]) -> int:
    if as_json:
        env = S.envelope(command, argv, 1, "", message)
        print(json.dumps(env, indent=2, sort_keys=True, default=str))
    else:
        print(f"error: {message}", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="memory_engine",
        description="mem20 memory engine 4.0 substrate",
    )
    p.add_argument("--json", action="store_true",
                   help="emit the fleet JSON envelope instead of human output")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="ledger counts and label coverage")
    sub.add_parser("health", help="one dict describing the whole substrate")

    pr = sub.add_parser("remember", help="store a grounded fact")
    pr.add_argument("--topic", required=True)
    pr.add_argument("--content", required=True)
    pr.add_argument("--epistemic-status", required=True,
                    help="how this claim was learned (observed, inferred, "
                         "user_stated, hypothesis, agent_generated, unlabeled)")
    pr.add_argument("--tags", default="")
    pr.add_argument("--actor", default="agent")
    pr.add_argument("--confidence", type=float)

    pc = sub.add_parser("recall", help="recall facts, label intact")
    pc.add_argument("--topic")
    pc.add_argument("--tags", default="")
    pc.add_argument("--k", type=int, default=5)

    pv = sub.add_parser("veto", help="may a plan rest on these fact ids?")
    pv.add_argument("--id", action="append", required=True, dest="ids")

    pg = sub.add_parser("guard", help="the same question via mem20crewz guardrails")
    pg.add_argument("--id", action="append", required=True, dest="ids")

    pn = sub.add_parser("namespace", help="the memory namespace an agent owns")
    pn.add_argument("--agent", required=True)

    ps = sub.add_parser("subsystem", help="is a subsystem installed, and what does it expose?")
    ps.add_argument("--name", required=True)

    pd = sub.add_parser("dream", help="open a dream lineage and report its artifact")
    pd.add_argument("--seed", required=True)
    pd.add_argument("--kind", default="active")

    pa = sub.add_parser("validate", help="validate a glTF/GLB artifact")
    pa.add_argument("--path", required=True)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)
    as_json = bool(args.json)
    command = args.cmd

    try:
        if command == "status":
            return _emit(S.health(), as_json=as_json, command=command, argv=argv)

        if command == "health":
            return _emit(S.health(), as_json=as_json, command=command, argv=argv)

        if command == "remember":
            rec = S.remember_fact(
                args.topic, args.content,
                epistemic_status=args.epistemic_status,
                tags=[t for t in args.tags.split(",") if t],
                actor=args.actor,
                confidence=args.confidence,
            )
            return _emit({"id": rec["id"], "topic": rec["topic"],
                          "epistemic_status": rec["epistemic_status"]},
                         as_json=as_json, command=command, argv=argv)

        if command == "recall":
            rows = S.recall_facts(
                args.topic,
                tags=[t for t in args.tags.split(",") if t],
                k=args.k,
            )
            return _emit(rows, as_json=as_json, command=command, argv=argv)

        if command == "veto":
            return _emit(S.veto_plan(args.ids), as_json=as_json,
                         command=command, argv=argv)

        if command == "guard":
            return _emit(S.guard_plan(args.ids), as_json=as_json,
                         command=command, argv=argv)

        if command == "namespace":
            return _emit({"agent": args.agent,
                          "namespace": S.namespace_for_agent(args.agent)},
                         as_json=as_json, command=command, argv=argv)

        if command == "subsystem":
            return _emit(S.subsystem_status(args.name), as_json=as_json,
                         command=command, argv=argv)

        if command == "dream":
            return _emit(S.dream_lineage(args.seed, kind=args.kind),
                         as_json=as_json, command=command, argv=argv)

        if command == "validate":
            result = S.validate_artifact(args.path)
            code = _emit(result, as_json=as_json, command=command, argv=argv)
            # A failed validation is a real failure: exit non-zero so a script
            # cannot mistake "invalid artifact" for success.
            return code if result["ok"] else 1

    except S.SubstrateError as exc:
        return _fail(str(exc), as_json=as_json, command=command, argv=argv)
    except ValueError as exc:
        # The engine refuses an undeclared/invalid epistemic basis with ValueError.
        return _fail(str(exc), as_json=as_json, command=command, argv=argv)

    return _fail(f"unknown command {command!r}", as_json=as_json,
                 command=command, argv=argv)


if __name__ == "__main__":
    sys.exit(main())
