"""mem20webgpuz command-line surface.

Commands
--------
``inspect``      runtime, roadmap and config snapshot
``capabilities`` hardware probe and backend availability
``run``          execute one request (JSON argument or ``-`` for stdin)
``simulate``     replay the roadmap's failure modes
``benchmark``    measure real latency/throughput
``jobs``         list recent jobs
``job``          show one job
``cancel``       cancel a job
``events``       dump the event log
``feedback``     record a feedback signal
``serve``        start the HTTP API
``conformance``  run the estate's conformance gate for this subsystem

Exit codes: ``0`` success, ``1`` a domain/validation error, ``2`` usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence

from . import webgpu
from .api import Api
from .config import WebGPUConfig
from .errors import WebGPUError
from .runtime import Runtime

__all__ = ["main", "build_parser"]


def _global_flags() -> argparse.ArgumentParser:
    """The flags that apply to every command.

    Declared on a parent parser and inherited by each subcommand, so
    ``mem20webgpuz --json inspect`` and ``mem20webgpuz inspect --json`` both
    work. Requiring one specific position is a papercut with no upside.
    """
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--data-dir", default=None, help="state directory (default .rmdata)")
    parent.add_argument("--json", action="store_true", help="emit compact JSON")
    return parent


def build_parser() -> argparse.ArgumentParser:
    common = _global_flags()
    parser = argparse.ArgumentParser(
        prog="mem20webgpuz",
        description="WebGPU compute studio: honest backend selection against probed hardware.",
        parents=[common],
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("inspect", parents=[common], help="runtime, roadmap and config snapshot")
    sub.add_parser(
        "capabilities", parents=[common], help="hardware probe and backend availability"
    )

    run = sub.add_parser("run", parents=[common], help="execute one request")
    run.add_argument("request", nargs="?", default="{}", help="JSON request, or - for stdin")
    run.add_argument("--idem", default=None, help="idempotency key")

    sub.add_parser("simulate", parents=[common], help="replay failure modes")

    bench = sub.add_parser("benchmark", parents=[common], help="measure latency and throughput")
    bench.add_argument("--runs", type=int, default=5)

    jobs = sub.add_parser("jobs", parents=[common], help="list recent jobs")
    jobs.add_argument("--limit", type=int, default=20)

    job = sub.add_parser("job", parents=[common], help="show one job")
    job.add_argument("job_id")

    cancel = sub.add_parser("cancel", parents=[common], help="cancel a job")
    cancel.add_argument("job_id")

    events = sub.add_parser("events", parents=[common], help="dump the event log")
    events.add_argument("--after", type=int, default=0)

    feedback = sub.add_parser("feedback", parents=[common], help="record a feedback signal")
    feedback.add_argument("signal")
    feedback.add_argument("value", type=float)
    feedback.add_argument("--note", default="")

    serve = sub.add_parser("serve", parents=[common], help="start the HTTP API")
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)

    conf = sub.add_parser("conformance", parents=[common], help="run the estate conformance gate")
    conf.add_argument("--all", action="store_true", help="check every subsystem")

    return parser


def _emit(payload: Any, compact: bool) -> None:
    if compact:
        print(json.dumps(payload, separators=(",", ":"), default=str))
    else:
        print(json.dumps(payload, indent=2, default=str))


def _load_request(raw: str) -> dict[str, Any]:
    text = sys.stdin.read() if raw == "-" else raw
    try:
        parsed = json.loads(text or "{}")
    except json.JSONDecodeError as exc:
        raise WebGPUError(f"request is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise WebGPUError("request must be a JSON object")
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "conformance":
        import subprocess
        from pathlib import Path

        gate = Path(__file__).resolve().parents[2] / "scripts" / "renovation" / "conformance.py"
        cmd = [sys.executable, str(gate)]
        cmd += ["--all"] if args.all else ["mem20webgpuz"]
        return subprocess.call(cmd)

    config = WebGPUConfig.from_env()
    if args.data_dir:
        config = WebGPUConfig(
            data_dir=__import__("pathlib").Path(args.data_dir),
            host=config.host,
            port=config.port,
            max_concurrent=config.max_concurrent,
            queue_timeout=config.queue_timeout,
            max_workgroups=config.max_workgroups,
            max_payload_bytes=config.max_payload_bytes,
            log_level=config.log_level,
        )

    try:
        if args.command == "capabilities":
            probe = webgpu.probe_hardware()
            chosen, alternatives = webgpu.select_backend({}, probe)
            _emit(
                {
                    "probe": probe.to_dict(),
                    "chosen": chosen.to_dict(),
                    "alternatives": [b.to_dict() for b in alternatives],
                },
                args.json,
            )
            return 0

        runtime = Runtime(config)

        if args.command == "inspect":
            _emit(runtime.inspect(), args.json)
        elif args.command == "run":
            result = runtime.run(_load_request(args.request), args.idem)
            _emit(result.to_dict(), args.json)
        elif args.command == "simulate":
            _emit(runtime.simulate(), args.json)
        elif args.command == "benchmark":
            _emit(runtime.benchmark(args.runs), args.json)
        elif args.command == "jobs":
            _emit(runtime.store.list_jobs(args.limit), args.json)
        elif args.command == "job":
            _emit(runtime.store.require_job(args.job_id), args.json)
        elif args.command == "cancel":
            _emit({"cancelled": runtime.cancel(args.job_id)}, args.json)
        elif args.command == "events":
            _emit(runtime.store.events(args.after), args.json)
        elif args.command == "feedback":
            runtime.store.feedback(args.signal, args.value, args.note)
            _emit({"ok": True}, args.json)
        elif args.command == "serve":
            api = Api(runtime)
            host, port = api.start(args.host, args.port)
            print(f"mem20webgpuz listening on http://{host}:{port}", flush=True)
            try:
                import time

                while True:
                    time.sleep(3600)
            except KeyboardInterrupt:
                api.stop()
        else:  # pragma: no cover - argparse enforces the set
            raise WebGPUError(f"unknown command: {args.command}")
        return 0
    except WebGPUError as exc:
        print(json.dumps(exc.to_dict(), indent=2), file=sys.stderr)
        return 1
