#!/usr/bin/env python3
"""Settle the tool-count decomposition by counting, not by asserting.

Three guards in this repository state the tool surface and they disagreed:

  Python runtime   tools/list returns 272
  Perl SDK         "270 tools across 27 domains" (sdk/perl/AUDIT.md)
  C++ SDK          static_assert(kToolCount == 270) (before 2026-11-01)

and the *decomposition* disagreed more than the total did. The C++ header
claimed 265 domain tools + 5 a2a_* = 270. The runtime's own partition implied
263 in the remaining groups. The Perl audit said 268 + 2 infra.

This script answers the question the three of them were guessing at: given the
names a live server actually advertises, how do they split?

    total          every name in tools/list
    a2a_*          the A2A transport layer, which is not a domain
    remainder      total - a2a_*
    prefixes       distinct first-`_` components, which is NOT the domain count

The last line is the one that caused the confusion. A prefix is a naming
convention; a domain is a registration group. `cog_*`, `tot_*`, `beam_*`,
`react_*`, `least_*`, `reflexion_*` and `cognitive_*` are seven prefixes and one
domain. Counting prefixes and calling the result "domains" is how 37 became 27
in one document and 38 in another.

Usage:
    python3 scripts/tool_decomposition.py
    python3 scripts/tool_decomposition.py --json
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def live_names() -> list[str]:
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "launcher.py")],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, bufsize=1, cwd=str(ROOT),
    )

    def send(o: dict) -> None:
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(o) + "\n")
        proc.stdin.flush()

    def recv() -> dict:
        assert proc.stdout is not None
        while True:
            line = proc.stdout.readline()
            if not line:
                raise SystemExit("EOF from server before tools/list returned")
            line = line.strip()
            if line.startswith("{"):
                return json.loads(line)

    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "tool_decomposition", "version": "1"}}})
        recv()
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        return [t["name"] for t in recv()["result"]["tools"]]
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def main() -> int:
    names = live_names()
    a2a = [n for n in names if n.startswith("a2a_")]
    rest = [n for n in names if not n.startswith("a2a_")]
    prefixes_all = sorted({n.split("_")[0] for n in names})
    prefixes_rest = sorted({n.split("_")[0] for n in rest})

    result = {
        "total": len(names),
        "a2a": len(a2a),
        "remainder": len(rest),
        "prefixes_all": len(prefixes_all),
        "prefixes_remainder": len(prefixes_rest),
        "unique": len(set(names)),
    }

    if "--json" in sys.argv:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print(f"total tools            {result['total']}")
    print(f"  a2a_* (transport)    {result['a2a']}")
    print(f"  remainder            {result['remainder']}")
    print(f"distinct names         {result['unique']}")
    print(f"name prefixes (all)    {result['prefixes_all']}")
    print(f"name prefixes (rest)   {result['prefixes_remainder']}")
    print()
    print(f"{result['remainder']} + {result['a2a']} = {result['total']}")
    print("A prefix is not a domain. The domain count comes from registration")
    print("groups, not from splitting names on the first underscore.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
