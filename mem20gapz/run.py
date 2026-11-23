#!/usr/bin/env python3
"""CLI entry point for mem20gapz."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure repo root is on sys.path for sibling imports
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from mem20gapz.core import (
    Capability,
    CapabilityGap,
    BridgingAction,
    GapCluster,
    RequiredCapability,
    CapabilityTaxonomy,
    normalize_capability,
    compute_gaps,
    generate_bridging_strategies,
    cluster_gaps,
    rank_bridging_actions,
    simulate_acquisition,
    detect_drift,
    family_capability_gap_mapper,
)

DEFAULT_PORT = 8768


def load_roadmap(path=None):
    p = Path(path or Path(__file__).with_name("roadmap.json"))
    return json.loads(p.read_text())


def _read_request(argv):
    """Read request from stdin or --request argument."""
    import sys
    if not sys.stdin.isatty():
        return json.load(sys.stdin)
    # Check for --request flag
    for i, arg in enumerate(argv):
        if arg == "--request" and i + 1 < len(argv):
            return json.loads(argv[i + 1])
    return {}


def cmd_run(argv):
    """Run a capability gap mapper request."""
    request = _read_request(argv)
    rid = 206  # default to full pipeline
    for i, arg in enumerate(argv):
        if arg == "--rid" and i + 1 < len(argv):
            rid = int(argv[i + 1])
            break
    result = family_capability_gap_mapper(rid, request)
    print(json.dumps(result, indent=2, default=str))


def cmd_serve(argv):
    """Start HTTP server."""
    from mem20core.core import Runtime, Api
    rm = load_roadmap()
    rt = Runtime(rm, ".gapdata")
    api = Api(rt)
    addr = api.start("127.0.0.1", DEFAULT_PORT)
    print(f"RM-{rm['global_id']:03d} listening on http://{addr[0]}:{addr[1]}", flush=True)
    try:
        while True:
            import time
            time.sleep(3600)
    except KeyboardInterrupt:
        api.stop()


def cmd_simulate(argv):
    """Run simulator."""
    from mem20core.core import Runtime, simulator
    rm = load_roadmap()
    rt = Runtime(rm, ".gapdata")
    result = simulator(rt)
    print(json.dumps(result, indent=2, default=str))


def cmd_benchmark(argv):
    """Run benchmark."""
    from mem20core.core import Runtime, benchmark
    rm = load_roadmap()
    rt = Runtime(rm, ".gapdata")
    runs = 5
    for i, arg in enumerate(argv):
        if arg == "--runs" and i + 1 < len(argv):
            runs = int(argv[i + 1])
            break
    result = benchmark(rt, runs)
    print(json.dumps(result, indent=2, default=str))


def cmd_probe(argv):
    """Probe ecosystem peers."""
    try:
        from mem20gapz.ecosystem import probe
    except ImportError:
        print(json.dumps({"ok": False, "error": "ecosystem module not found"}, indent=2))
        return
    result = probe()
    print(json.dumps(result, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(prog="mem20gapz")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run")
    p.add_argument("--rid", type=int, default=206, help="Request ID (201-206)")
    p.add_argument("--request", help="JSON request string")

    p = sub.add_parser("serve")
    p.add_argument("--port", type=int, default=DEFAULT_PORT)

    sub.add_parser("simulate")

    p = sub.add_parser("benchmark")
    p.add_argument("--runs", type=int, default=5)

    sub.add_parser("probe")

    args = parser.parse_args(sys.argv[1:])

    if args.cmd == "run":
        cmd_run(sys.argv[2:])
    elif args.cmd == "serve":
        cmd_serve(sys.argv[2:])
    elif args.cmd == "simulate":
        cmd_simulate(sys.argv[2:])
    elif args.cmd == "benchmark":
        cmd_benchmark(sys.argv[2:])
    elif args.cmd == "probe":
        cmd_probe(sys.argv[2:])


if __name__ == "__main__":
    main()