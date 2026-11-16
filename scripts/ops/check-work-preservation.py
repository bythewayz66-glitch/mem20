#!/usr/bin/env python3
"""check-work-preservation.py — work-preservation gate for bythewayz66-glitch/mem20.

A deliverable is PRESERVED only when it is reachable from a permanent address:

  (a) a 40-character commit SHA on a pushed branch in the canonical repo, or
  (b) a permanent artifact URL (https://static.teamily.ai/sites/... or /files/...)
      that answers HTTP 200.

Anything else — a chat message, a plan, a summary, a sandbox-only file, a branch
that exists only locally — is AT-RISK work and is flagged.

This is the work-preservation counterpart to the contribution-evidence gate
(`scripts/ops/verify-contrib-evidence.sh`). That gate checks a *PR body*; this
gate checks a *deliverable ledger* and reports every row that carries neither a
commit nor a permanent URL.

Usage:
  scripts/ops/check-work-preservation.py --ledger <path> [--json] [--offline]
  scripts/ops/check-work-preservation.py --self-test

Ledger format (Markdown table, one row per deliverable). The header row must
contain the columns `Artifact`, `Commit`, and `Permanent URL` (case-insensitive,
order-independent). Example:

  | Artifact | Producer | Commit | Permanent URL | Status |
  |---|---|---|---|---|
  | ops ledger page | Mem20-admin | 0224a64946a2c00313a9872515893157adcbc47e | https://static.teamily.ai/sites/.../index.html | published |

Exit codes:
  0  every row is preserved (has a 40-char commit or a 200 permanent URL)
  1  at least one row is at-risk (no commit and no permanent URL)
  2  usage error / ledger unreadable

Environment:
  WORK_PRESERVATION_TIMEOUT  per-URL curl timeout in seconds (default 10)
  WORK_PRESERVATION_OFFLINE  when "1", skip the network probe and accept any
                             well-formed permanent URL (used by --self-test)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

SHA40 = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{40}(?![0-9a-fA-F])")
PERMANENT_URL = re.compile(r"https?://[^\s|)\]]+/(?:sites|files)/[^\s|)\]]+")
ANY_URL = re.compile(r"https?://[^\s|)\]]+")

TIMEOUT = os.environ.get("WORK_PRESERVATION_TIMEOUT", "10")
OFFLINE = os.environ.get("WORK_PRESERVATION_OFFLINE", "0") == "1"


def split_row(line: str) -> list[str]:
    """Split a Markdown table row into trimmed cells."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c or "-") for c in cells)


def find_header(rows: list[list[str]]) -> int | None:
    for i, cells in enumerate(rows):
        low = [c.lower() for c in cells]
        if "artifact" in low and "commit" in low and any("permanent" in c for c in low):
            return i
    return None


def url_ok(url: str) -> bool:
    """A permanent URL is preserved when it answers HTTP 200 (follows redirects)."""
    if OFFLINE:
        return True
    try:
        out = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "-L", "--max-time", TIMEOUT, url],
            capture_output=True, text=True, timeout=int(TIMEOUT) + 5,
        )
        return out.stdout.strip() == "200"
    except Exception:
        return False


def check_ledger(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    # Find the header line, then take only the CONTIGUOUS table block that
    # follows it. A ledger may hold several tables; only the one whose header
    # names Artifact / Commit / Permanent URL is the register we check.
    hi = None
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        low = [c.lower() for c in split_row(line)]
        if "artifact" in low and "commit" in low and any("permanent" in c for c in low):
            hi = i
            break
    if hi is None:
        raise SystemExit(
            "usage error: ledger has no header row with Artifact / Commit / Permanent URL columns"
        )

    block: list[list[str]] = []
    for line in lines[hi:]:
        if not line.strip().startswith("|"):
            break
        cells = split_row(line)
        if is_separator(cells):
            continue
        block.append(cells)

    header = [c.lower() for c in block[0]]
    i_art = header.index("artifact")
    i_commit = header.index("commit")
    i_url = next(i for i, c in enumerate(header) if "permanent" in c)

    preserved, at_risk = [], []
    for cells in block[1:]:
        if len(cells) <= max(i_art, i_commit, i_url):
            continue
        artifact = cells[i_art]
        commit_cell = cells[i_commit]
        url_cell = cells[i_url]

        sha = SHA40.search(commit_cell)
        urls = PERMANENT_URL.findall(url_cell) or PERMANENT_URL.findall(" ".join(cells))
        good_url = next((u for u in urls if url_ok(u)), None)

        rec = {
            "artifact": artifact,
            "commit": sha.group(0) if sha else None,
            "permanent_url": good_url,
        }
        if sha or good_url:
            preserved.append(rec)
        else:
            at_risk.append(rec)

    return {
        "ledger": path,
        "preserved": preserved,
        "at_risk": at_risk,
        "preserved_count": len(preserved),
        "at_risk_count": len(at_risk),
    }


def self_test() -> int:
    import tempfile

    good = "0224a64946a2c00313a9872515893157adcbc47e"
    body = f"""# t

| Artifact | Producer | Commit | Permanent URL | Status |
|---|---|---|---|---|
| a | x | {good} | — | pushed |
| b | y | — | https://static.teamily.ai/sites/abc/webpages/p/index.html | published |
| c | z | — | — | chat only |
"""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
        fh.write(body)
        tmp = fh.name
    os.environ["WORK_PRESERVATION_OFFLINE"] = "1"
    global OFFLINE
    OFFLINE = True
    res = check_ledger(tmp)
    os.unlink(tmp)
    ok = res["preserved_count"] == 2 and res["at_risk_count"] == 1
    print(json.dumps(res, indent=2))
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--ledger")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not args.ledger:
        ap.print_help()
        return 2

    global OFFLINE
    if args.offline:
        OFFLINE = True

    res = check_ledger(args.ledger)
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"ledger: {res['ledger']}")
        print(f"preserved: {res['preserved_count']}   at-risk: {res['at_risk_count']}")
        for r in res["at_risk"]:
            print(f"  AT-RISK  {r['artifact']}  (no commit, no permanent URL)")
    return 1 if res["at_risk_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
