"""CLI for the event stream superhighway.

Every subcommand does real work against the real estate: ``publish`` routes an
event and persists it, ``report`` reads the stream and the substrate it depends
on, ``verify`` round-trips the memory engine, ``inventory`` reads the measured
tool inventory, and ``search`` decomposes a compound question about the stream.

    python -m mem20eventstreamsuperhighwayz publish --stream orders \
        --type order.created --payload '{"id": 7}' --key o-7
    python -m mem20eventstreamsuperhighwayz report --stream orders
    python -m mem20eventstreamsuperhighwayz verify
    python -m mem20eventstreamsuperhighwayz inventory
    python -m mem20eventstreamsuperhighwayz search "what is the p95 latency and which partition is hot"
"""
from __future__ import annotations

import argparse
import json
import sys

from . import domain, integration


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True, default=str))


def _cmd_publish(args) -> int:
    stream = domain.create_stream(args.stream)
    payload = json.loads(args.payload)
    out = integration.publish_and_persist(
        stream,
        args.type,
        payload,
        key=args.key,
        announce_to_fleet=not args.no_announce,
    )
    _print(out)
    return 0


def _cmd_report(args) -> int:
    stream = domain.create_stream(args.stream)
    for i in range(args.events):
        domain.publish(stream, args.type, {"n": i})
    for sub in args.subscriber:
        domain.subscribe(stream, sub)
    _print(integration.stream_report(stream, window_s=args.window))
    return 0


def _cmd_verify(args) -> int:
    report = integration.verify_memory_integrity()
    _print(report)
    return 0 if report.get("roundtrip_ok") == report.get("checked") else 1


def _cmd_inventory(args) -> int:
    _print(integration.inventory_counts())
    return 0


def _cmd_search(args) -> int:
    _print(integration.search_events(args.query, k=args.k))
    return 0


def _cmd_identity(args) -> int:
    _print(integration.identity_report())
    return 0


def _cmd_compact(args) -> int:
    _print(integration.compact_payload([float(v) for v in args.values], bits=args.bits))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="mem20eventstreamsuperhighwayz",
        description="Route typed events across local, edge and cloud runtimes.",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("publish", help="publish an event, persist it, announce it")
    p.add_argument("--stream", default="default")
    p.add_argument("--type", required=True)
    p.add_argument("--payload", default="{}")
    p.add_argument("--key", default=None)
    p.add_argument("--no-announce", action="store_true")
    p.set_defaults(func=_cmd_publish)

    p = sub.add_parser("report", help="operational report for a stream")
    p.add_argument("--stream", default="default")
    p.add_argument("--type", default="probe")
    p.add_argument("--events", type=int, default=3)
    p.add_argument("--subscriber", action="append", default=[])
    p.add_argument("--window", type=int, default=60)
    p.set_defaults(func=_cmd_report)

    p = sub.add_parser("verify", help="round-trip the memory engine")
    p.set_defaults(func=_cmd_verify)

    p = sub.add_parser("inventory", help="measured estate tool inventory counts")
    p.set_defaults(func=_cmd_inventory)

    p = sub.add_parser("search", help="multi-hop search over the event log")
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
