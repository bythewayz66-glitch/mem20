#!/usr/bin/env python3
"""Poll the MCP server's /ready endpoint and report what it says.

`mcp/health.py` serves /health, /ready and /metrics. /ready returns
{"ready": bool(tools), "tools": len(tools)} -- the live registered tool count.
It is correct and, as of 2026-11-01, nothing polls it: the systemd unit has
Restart=always and no readiness gate, so a process that is up but has
registered zero tools is indistinguishable from a healthy one to the
supervisor.

This script is the poll. It is not wired into the unit, because a readiness
gate that polls the wrong port fails closed and takes the service down, and
the port is currently an environment variable with a default. See TD-10 in
2.0_roadmap/tech_debt_register.md.

Usage:
    python3 scripts/probe_ready.py                    # default port
    python3 scripts/probe_ready.py --port 8765
    python3 scripts/probe_ready.py --expect-tools 272 # also assert the count
    python3 scripts/probe_ready.py --wait 30          # retry for 30s

Exit codes:
    0  ready, and the tool count matches --expect-tools if given
    1  not ready, or the count did not match
    2  could not reach the endpoint
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

# Must match mcp/server.py:1090, which reads the same variable with the same
# default. A probe that defaults to a different port than the server binds is
# the failure mode TD-10 warns about: it fails closed and looks like an outage.
DEFAULT_PORT = int(os.environ.get("MEM20_HEALTH_PORT", "8080"))


def probe(port: int, timeout: float) -> dict:
    url = f"http://127.0.0.1:{port}/ready"
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--expect-tools", type=int, default=None)
    ap.add_argument("--wait", type=float, default=0.0,
                    help="retry for this many seconds before giving up")
    ap.add_argument("--timeout", type=float, default=2.0)
    args = ap.parse_args()

    deadline = time.monotonic() + args.wait
    last_err: str | None = None
    while True:
        try:
            body = probe(args.port, args.timeout)
            break
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
            last_err = str(e)
            if time.monotonic() >= deadline:
                print(f"UNREACHABLE 127.0.0.1:{args.port}/ready: {last_err}")
                return 2
            time.sleep(0.5)

    ready = bool(body.get("ready"))
    tools = body.get("tools")
    print(f"ready={ready} tools={tools}")

    if not ready:
        print("NOT READY: the server is up but has registered no tools")
        return 1

    if args.expect_tools is not None and tools != args.expect_tools:
        print(f"MISMATCH: expected {args.expect_tools} tools, server reports {tools}")
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
