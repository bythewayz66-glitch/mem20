#!/usr/bin/env python3
"""mem20 Gateway — command line surface.

Every subcommand here exercises real relay logic from ``gateway.routing``; none
of them is a help-printing stub. The subcommands map one-to-one onto the
decisions a relay has to make:

  screen    — may this payload cross the fleet boundary at all?
  route     — full decision: screen + target resolution + asset budget
  budget    — is an asset claim within its family's triangle band?
  verify    — is the store this message cites actually intact?
  inventory — which subsystems exist to route to?
  agents    — the fleet registry (register / list / broadcast / read)

Run as ``python -m gateway`` or via the ``mem20-gateway`` console script.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import routing


def _emit(payload: dict, as_json: bool) -> int:
    """Print a result and return the process exit code.

    Exit codes are part of the contract: 0 = permitted/ok, 1 = refused. A
    caller can therefore gate on the exit status without parsing stdout.
    """
    if as_json:
        print(json.dumps(payload, indent=2, default=str))
    else:
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                print(f"{key}: {json.dumps(value, default=str)}")
            else:
                print(f"{key}: {value}")
    return 0 if payload.get("allowed", payload.get("ok", True)) else 1


def cmd_screen(args: argparse.Namespace) -> int:
    verdict = routing.screen_payload(args.text, min_confidence=args.min_confidence)
    return _emit(verdict.to_dict(), args.json)


def cmd_route(args: argparse.Namespace) -> int:
    decision = routing.route(
        args.message,
        args.target,
        family=args.family,
        triangles=args.triangles,
        lod=args.lod,
        tier=args.tier,
        inventory_path=args.inventory,
        require_known_target=args.require_known_target,
    )
    return _emit(decision.to_dict(), args.json)


def cmd_budget(args: argparse.Namespace) -> int:
    result = routing.check_asset_budget(
        args.family, args.triangles, lod=args.lod, tier=args.tier
    )
    return _emit(result, args.json)


def cmd_verify(args: argparse.Namespace) -> int:
    result = routing.verify_store(args.engine_dir)
    return _emit(result, args.json)


def cmd_inventory(args: argparse.Namespace) -> int:
    result = routing.inventory_subsystems(args.inventory)
    if args.contains:
        result["contains"] = args.contains
        result["match"] = routing.target_is_known(args.contains, args.inventory)
        result["ok"] = result["ok"] and result["match"]
    return _emit(result, args.json)


def cmd_agents(args: argparse.Namespace) -> int:
    """Fleet registry operations, delegated to the existing relay module."""
    from . import hermes_gateway as hg

    if args.action == "register":
        record = hg.register_agent(name=args.name, location=args.location)
        return _emit({"ok": True, "agent": record}, args.json)
    if args.action == "list":
        names = hg.load_names()
        return _emit({"ok": True, "count": len(names), "agents": names}, args.json)
    if args.action == "broadcast":
        entry = hg.broadcast(args.message, agent_name=args.agent_name,
                             target=args.target)
        return _emit({"ok": True, "entry": entry}, args.json)
    if args.action == "read":
        messages = hg.read_messages(since=args.since, agent=args.agent,
                                    limit=args.limit)
        return _emit({"ok": True, "count": len(messages), "messages": messages},
                     args.json)
    return _emit({"ok": False, "error": f"unknown action {args.action}"}, args.json)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mem20-gateway",
        description="mem20 Gateway — relay routing, screening and fleet registry",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("screen", help="screen a payload for secrets before relaying")
    p.add_argument("text", help="payload text to screen")
    p.add_argument("--min-confidence", default="low",
                   choices=["low", "medium", "high"])
    p.set_defaults(func=cmd_screen)

    p = sub.add_parser("route", help="full relay decision for a message and target")
    p.add_argument("message", help="message body")
    p.add_argument("target", help="target subsystem or agent")
    p.add_argument("--family", help="asset family, if the message carries an asset claim")
    p.add_argument("--triangles", type=int, help="claimed triangle count")
    p.add_argument("--lod", type=int, default=0)
    p.add_argument("--tier", default="standard")
    p.add_argument("--inventory", help="path to toolchest inventory.json")
    p.add_argument("--require-known-target", action="store_true",
                   help="refuse if the target is absent from the estate inventory")
    p.set_defaults(func=cmd_route)

    p = sub.add_parser("budget", help="check an asset claim against its family band")
    p.add_argument("family")
    p.add_argument("triangles", type=int)
    p.add_argument("--lod", type=int, default=0)
    p.add_argument("--tier", default="standard")
    p.set_defaults(func=cmd_budget)

    p = sub.add_parser("verify", help="verify the memory engine store round-trips")
    p.add_argument("--engine-dir", help="path to memory_engine")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("inventory", help="list subsystems known to the estate")
    p.add_argument("--inventory", help="path to toolchest inventory.json")
    p.add_argument("--contains", help="check whether a subsystem is present")
    p.set_defaults(func=cmd_inventory)

    p = sub.add_parser("agents", help="fleet registry operations")
    p.add_argument("action", choices=["register", "list", "broadcast", "read"])
    p.add_argument("--name", "-n")
    p.add_argument("--location", "-l")
    p.add_argument("--message", "-m")
    p.add_argument("--agent-name", "-a")
    p.add_argument("--target", "-t", default="telegram_channel")
    p.add_argument("--since")
    p.add_argument("--agent")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_agents)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
