#!/usr/bin/env python3
"""Regenerate the README tool-domain table from the live MCP surface.

The table in README.md is a claim about what the server advertises. It was
maintained by hand, and by 2026-11-01 it had drifted in four ways at once:

  * the heading said "Tool domains (27)" while the body said "the 29 rows
    below" and the table had 29 rows;
  * the body said "270 total" while the server advertised 272;
  * the column summed to 257, which is a figure the project retired in
    September;
  * individual rows were stale (memory_* said 49, the server serves 52).

This script asks the server, groups by the first `_` component of each tool
name, and prints the table. It does not sum by hand and it does not read the
README -- the README is the thing being checked.

Usage:
    python3 scripts/gen_tool_table.py            # print the table
    python3 scripts/gen_tool_table.py --check    # exit 1 if README disagrees

The `--check` mode is what CI runs: it parses the table out of README.md,
compares every row against the live surface, and fails on any difference.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def live_tool_names() -> list[str]:
    """Ask a real server for its tools/list, over stdio, and return the names."""
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "launcher.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
        cwd=str(ROOT),
    )

    def send(obj: dict) -> None:
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(obj) + "\n")
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
        send({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "gen_tool_table", "version": "1"},
            },
        })
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


def group(names: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for n in names:
        counts[n.split("_")[0]] = counts.get(n.split("_")[0], 0) + 1
    return counts


def readme_rows() -> tuple[list[tuple[str, int]], int | None]:
    """Parse the prefix table out of README.md: (rows, stated total)."""
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    rows: list[tuple[str, int]] = []
    total: int | None = None
    for line in text.splitlines():
        m = re.match(r"^\|\s*`([a-z0-9_]+)_\*`[^|]*\|\s*(\d+)\s*\|", line)
        if m:
            rows.append((m.group(1), int(m.group(2))))
            continue
        m = re.match(r"^\|\s*\*\*total\*\*\s*\|\s*\*\*(\d+)\*\*", line)
        if m:
            total = int(m.group(1))
    return rows, total


def main() -> int:
    names = live_tool_names()
    counts = group(names)
    total = sum(counts.values())

    if "--check" in sys.argv:
        rows, stated = readme_rows()
        problems: list[str] = []
        if not rows:
            problems.append("README.md: no prefix table found")
        live = dict(counts)
        for prefix, n in rows:
            if prefix not in live:
                problems.append(f"README.md lists `{prefix}_*` = {n}; the server has no such prefix")
            elif live[prefix] != n:
                problems.append(f"README.md says `{prefix}_*` = {n}; the server serves {live[prefix]}")
        listed = {p for p, _ in rows}
        for prefix in sorted(set(live) - listed):
            problems.append(f"README.md omits `{prefix}_*` = {live[prefix]}")
        if stated is not None and stated != total:
            problems.append(f"README.md states a total of {stated}; the server serves {total}")
        if sum(n for _, n in rows) != total:
            problems.append(
                f"README.md's column sums to {sum(n for _, n in rows)}; the server serves {total}"
            )
        if problems:
            for p in problems:
                print(f"::error::{p}")
            return 1
        print(f"OK: README table matches the live surface ({total} tools, {len(counts)} prefixes)")
        return 0

    print(f"| Prefix | Tools |")
    print(f"|--------|------:|")
    for prefix, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"| `{prefix}_*` | {n} |")
    print(f"| **total** | **{total}** |")
    print(f"\n{total} tools across {len(counts)} prefixes", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
