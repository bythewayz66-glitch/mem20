"""CLI for the cross-runtime event lattice.

Every subcommand does real work against the real estate: ``emit`` emits an
event, links it causally, persists it and announces it; ``report`` merges
lattices and reports on the substrate; ``verify`` round-trips the memory
engine; ``inventory`` reads the measured tool inventory; ``search`` decomposes
a compound question about lattice history.

    python -m mem20crossruntimeeventlatticez emit --type click --payload '{"x": 1}' --lattice web
    python -m mem20crossruntimeeventlatticez report --lattice web
    python -m mem20crossruntimeeventlatticez verify
    python -m mem20crossruntimeeventlatticez inventory
    python -m mem20crossruntimeeventlatticez search "which runtime emitted the first failure and what did it cause"
"""
from __future__ import annotations

import argparse
import json
import sys

from . import domain, integration


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True, default=str))


def _cmd_emit(args) -> int:
    payload = json.loads(args.payload)
    parent = None
    if args.parent:
        parent = domain.emit("parent", {}, source=args.source)
        parent["id"] = args.parent
    out = integration.emit_and_record(
        args.type,
        payload,
        lattice=args.lattice,
        source=args.source,
        parent=parent,
        announce_to_fleet=not args.no_announce,
    )
    _print(out)
    return 0


def _cmd_report(args) -> int:
    lattices = []
    for i in range(args.lattices):
        events = [
            domain.emit(args.type, {"n": j}, source=args.source)
            for j in range(args.events)
        ]
        lattices.append({"events": events})
    _print(integration.lattice_report(lattices, name=args.lattice, window_s=args.window))
    return 0


def _cmd_verify(args) -> int:
    report = integration.verify_memory_integrity()
    _print(report)
    return 0 if report.get("roundtrip_ok") == report.get("checked") else 1


def _cmd_inventory(args) -> int:
    _print(integration.inventory_counts())
    return 0


def _cmd_search(args) -> int:
    _print(integration.search_history(args.query, k=args.k))
    return 0


def _cmd_identity(args) -> int:
    _print(integration.identity_report())
    return 0


def _cmd_compact(args) -> int:
    _print(integration.compact_payload([float(v) for v in args.values], bits=args.bits))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="mem20crossruntimeeventlatticez",
        description="Connect independent runtimes through typed events and causality.",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("emit", help="emit, link, persist and announce an event")
    p.add_argument("--type", required=True)
    p.add_argument("--payload", default="{}")
    p.add_argument("--lattice", default="default")
    p.add_argument("--source", default="local")
    p.add_argument("--parent", default=None, help="parent event id to link causally")
    p.add_argument("--no-announce", action="store_true")
    p.set_defaults(func=_cmd_emit)

    p = sub.add_parser("report", help="operational report for a merged lattice")
    p.add_argument("--lattice", default="default")
    p.add_argument("--type", default="probe")
    p.add_argument("--events", type=int, default=2)
    p.add_argument("--lattices", type=int, default=2)
    p.add_argument("--source", default="local")
    p.add_argument("--window", type=int, default=60)
    p.set_defaults(func=_cmd_report)

    p = sub.add_parser("verify", help="round-trip the memory engine")
    p.set_defaults(func=_cmd_verify)

    p = sub.add_parser("inventory", help="measured estate tool inventory counts")
    p.set_defaults(func=_cmd_inventory)

    p = sub.add_parser("search", help="multi-hop search over lattice history")
    p.add_argument("query")
    p.add_argument("--k", type=int, default=5)
    p.set_defaults(func=_cmd_search)

    p = sub.add_parser("identity", help="pinned blocks and namespaces")
    p.set_defaults(func=_cmd_identity)

    p = sub.add_parser("compact", help="quantize a numeric payload for the wire")
    p.add_argument("values", nargs="+")
    p.add_argument("--bits", type=int, default=8)
    p.set_defaults(func=_cmd_compact)

    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
