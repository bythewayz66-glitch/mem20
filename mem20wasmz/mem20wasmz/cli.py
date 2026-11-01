"""Command line for the mem20wasmz WebAssembly component lab.

Subcommands:

  inspect    roadmap identity, phase count, and the component surface
  run        run one component request through the isolated runtime
  simulate   replay the simulator scenarios (success, malformed, overload, ...)
  benchmark  time N runs and report the measured numbers
  wiring     prove the six cross-module calls the 4.0 architecture rule requires

Every number printed by ``benchmark`` is measured in this process. Nothing is
estimated: if a measurement cannot be taken, the command says so and exits
non-zero rather than printing a plausible figure.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional

from . import wiring
from .core import (
    Api,
    Runtime,
    benchmark as run_benchmark,
    load_roadmap,
    simulator,
)

EXIT_OK = 0
EXIT_FAILED = 1

# The lab's own roadmap lives beside the package (mem20wasmz/roadmap.json).
# mem20core.load_roadmap() defaults to *its* roadmap.json, which does not exist
# in a source checkout, so the path is always passed explicitly.
ROADMAP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "roadmap.json")


def _emit(payload: Any) -> None:
    print(json.dumps(payload, indent=2, default=str))


def _runtime() -> Runtime:
    """A runtime over this lab's roadmap, with state in a scratch directory.

    The default ``.rmdata`` would write a SQLite file into whatever directory
    the command was run from; a scratch dir keeps the checkout clean.
    """
    return Runtime(load_roadmap(ROADMAP_PATH), data_dir=tempfile.mkdtemp(prefix="mem20wasmz-"))


def cmd_inspect(_args: argparse.Namespace) -> int:
    roadmap = load_roadmap(ROADMAP_PATH)
    phases = roadmap.get("phases") or []
    _emit(
        {
            "global_id": roadmap.get("global_id"),
            "title": roadmap.get("title"),
            "owner": roadmap.get("owner"),
            "lane": roadmap.get("lane"),
            "outcome": roadmap.get("outcome"),
            "phases": len(phases),
            "subphases": sum(len(p.get("subphases") or []) for p in phases),
        }
    )
    return EXIT_OK


def cmd_run(args: argparse.Namespace) -> int:
    try:
        request = json.loads(args.request)
    except json.JSONDecodeError as exc:
        _emit({"error": f"request is not valid JSON: {exc}"})
        return EXIT_FAILED
    runtime = _runtime()
    result = runtime.run(request)
    _emit({"result": result, "audit": wiring.describe_run(result)})
    return EXIT_OK


def cmd_simulate(_args: argparse.Namespace) -> int:
    runtime = _runtime()
    _emit(simulator(runtime))
    return EXIT_OK


def cmd_benchmark(args: argparse.Namespace) -> int:
    runtime = _runtime()
    started = time.perf_counter()
    report = run_benchmark(runtime, runs=args.runs)
    elapsed = time.perf_counter() - started
    _emit({"measured_wall_seconds": round(elapsed, 6), "report": report})
    return EXIT_OK


def cmd_wiring(_args: argparse.Namespace) -> int:
    _emit(wiring.self_check())
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mem20wasmz",
        description="WebAssembly component lab: language-neutral components with explicit interfaces and strong isolation.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    inspect = sub.add_parser("inspect", help="roadmap identity and component surface")
    inspect.set_defaults(func=cmd_inspect)

    run = sub.add_parser("run", help="run one component request")
    run.add_argument("request", help='JSON request, e.g. \'{"text":"demo","cache":false}\'')
    run.set_defaults(func=cmd_run)

    simulate = sub.add_parser("simulate", help="replay the simulator scenarios")
    simulate.set_defaults(func=cmd_simulate)

    bench = sub.add_parser("benchmark", help="time N runs and report measured numbers")
    bench.add_argument("--runs", type=int, default=5, help="number of runs (default 5)")
    bench.set_defaults(func=cmd_benchmark)

    wiring_cmd = sub.add_parser("wiring", help="prove the cross-module calls")
    wiring_cmd.set_defaults(func=cmd_wiring)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
