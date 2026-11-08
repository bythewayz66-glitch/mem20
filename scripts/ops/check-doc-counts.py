#!/usr/bin/env python3
"""Doc-count drift gate for mem20.

Fails when a **live** doc carries a **retired** tool/domain band instead of the
live pin in ``docs/surface.json``.

Why this exists
---------------
The tool surface has moved several times (257 -> 258-260 -> 265 -> 268 -> 270 ->
306 -> 311 tools; 26 -> 27 -> 38 -> 39 domains). Every move left prose behind
that still presents the old number as *current*. ``scripts/surface_manifest.py``
already checks a hand-listed set of current-facing docs, but that list is short
and the retired bands keep reappearing in subsystem READMEs, SDK docs and the
docs/ tree. This gate is the mechanical backstop: it scans the whole live-doc
surface for a retired band and fails the run.

The live pin is never hardcoded here
------------------------------------
The expected ``tools`` / ``domains`` values are read from ``docs/surface.json``,
which is generated from the live JSON-RPC ``tools/list`` response by
``scripts/surface_manifest.py``. A gate that pinned the number in a second place
would start drifting the moment the first place moved -- exactly the failure it
is meant to catch. If ``docs/surface.json`` is missing the gate exits 2 (cannot
run) rather than guessing.

What counts as a "live" doc
---------------------------
Only docs that describe the surface *as it is today* are in scope. Dated
records, audits, the immutable ``published/`` archive and generated snapshots
are **out of scope**: they are history, and rewriting their numbers would
falsify the record rather than correct it. The scope is:

  * ``docs/*.md`` (top level) and ``docs/hygiene/*.md``
  * ``docs/index.html`` and ``docs/dashboard.html``
  * every ``mem20*z/README.md`` subsystem entry doc
  * ``README.md``, ``SDKS.md``, ``toolchest/README.md``

Out of scope (excluded by prefix or exact path): ``published/``, ``docs/audit/``,
``docs/recon/``, ``docs/ops/``, ``docs/app/narrative/``, ``docs/app/deck/``,
``docs/renovation/``, ``ops/``, ``.sitemap/``, ``CHANGELOG.md``, ``DIARY.md``,
``failures.md``, ``AbsoluteTruth113.md``, ``toolchest/inventory.json``, and any
file whose name carries a ``YYYY-MM`` date stamp.

Retirement markers
------------------
A retired band is legal on a line that *names* it as retired, superseded,
historical, etc. The gate asks "is this presented as current?" and the only
machine-checkable proxy for that is the absence of a retirement marker on the
same line. Markers are line-local so every exemption is auditable by eye.

Usage
-----
    python3 scripts/ops/check-doc-counts.py            # gate (exit 1 on drift)
    python3 scripts/ops/check-doc-counts.py --list     # print the scope, then exit
    python3 scripts/ops/check-doc-counts.py --root DIR # scan a different checkout
    python3 scripts/ops/check-doc-counts.py --self-test

Exit codes: 0 = no drift, 1 = drift found, 2 = cannot run (no pin / bad root).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# The retired bands. These are the numbers that have been the live surface at
# some earlier HEAD and must never be presented as current again.
# --------------------------------------------------------------------------
RETIRED_TOOLS = ("257", "258", "259", "260", "265", "268", "270", "306")
RETIRED_DOMAINS = ("26", "27", "38")

# A retired band is legal on a line that names it as history. Line-local, so
# every exemption is auditable by eye.
RETIREMENT_MARKERS = (
    "retired",
    "predates",
    "superseded",
    "previous",
    "prior",
    "earlier",
    "historic",
    "before the",
    "no longer",
    "old value",
    "stale",
    "was ",
    "were ",
    "used to",
    "formerly",
    "legacy",
    "deprecated",
    "withdrawn",
    "banned",
)

# --------------------------------------------------------------------------
# Scope: live docs only.
# --------------------------------------------------------------------------
EXCLUDE_PREFIXES = (
    "published/",          # immutable delivery archive (MANIFEST-pinned)
    "docs/audit/",         # dated audits
    "docs/recon/",         # stale-file inventory + evidence
    "docs/ops/",           # dated ops logs
    "docs/app/narrative/", # dated serials
    "docs/app/deck/",      # dated deck records
    "docs/renovation/",    # in-flight 4.0 overhaul
    "ops/",                # dated ops records
    ".sitemap/",           # generated snapshot
)
EXCLUDE_FILES = {
    "CHANGELOG.md",        # history of earlier reconciles
    "DIARY.md",            # dated diary
    "failures.md",         # dated failure log
    "AbsoluteTruth113.md", # dated audit narrative
    "toolchest/inventory.json",  # generated snapshot
}
DATE_STAMP = re.compile(r"(19|20)\d{2}-\d{2}")  # YYYY-MM in the filename

# --------------------------------------------------------------------------
# Claim patterns. A retired band is a violation only when it is attached to the
# word "tools" / "domains" (or written as a tools/domains pair), so a bare
# number in geometry or a version string is never a false positive.
# --------------------------------------------------------------------------
TOOL_CLAIM = re.compile(
    r"(?<![-\w])(%s)\s+(?:(?:MCP|unique|real|distinct|registered|live)\s+){0,2}tools?\b"
    % "|".join(RETIRED_TOOLS),
    re.IGNORECASE,
)
DOMAIN_CLAIM = re.compile(
    r"(?<![-\w])(%s)\s+(?:(?:MCP|distinct|live)\s+)?domains?\b"
    % "|".join(RETIRED_DOMAINS),
    re.IGNORECASE,
)
PAIR_CLAIM = re.compile(
    r"(?<![-\w])(%s)\s*/\s*(%s)(?![-\w])"
    % ("|".join(RETIRED_TOOLS), "|".join(RETIRED_DOMAINS))
)
TABLE_TOOL_CLAIM = re.compile(
    r"MCP tools\s*\|\s*\*{0,2}(%s)\b" % "|".join(RETIRED_TOOLS), re.IGNORECASE
)

TEXT_SUFFIXES = (".md", ".html", ".htm")


def repo_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    return Path(__file__).resolve().parents[2]


def live_pin(root: Path) -> tuple[int, int]:
    """Read the live tools/domains pin from docs/surface.json."""
    surface = root / "docs" / "surface.json"
    if not surface.is_file():
        raise SystemExit(
            "cannot run: %s is missing; regenerate it with "
            "`python3 scripts/surface_manifest.py --write`" % surface
        )
    data = json.loads(surface.read_text(encoding="utf-8"))
    return int(data["tools"]), int(data["domains"])


def tracked_files(root: Path) -> list[str]:
    """Tracked paths, relative to the repo root."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise SystemExit("cannot run: `git ls-files` failed in %s (%s)" % (root, exc))
    return [line for line in out.splitlines() if line]


def in_scope(rel: str) -> bool:
    if not rel.endswith(TEXT_SUFFIXES):
        return False
    if rel in EXCLUDE_FILES:
        return False
    if rel.startswith(EXCLUDE_PREFIXES):
        return False
    if DATE_STAMP.search(Path(rel).name):
        return False
    if rel in ("README.md", "SDKS.md", "toolchest/README.md"):
        return True
    if rel in ("docs/index.html", "docs/dashboard.html"):
        return True
    if rel.startswith("docs/hygiene/") and rel.endswith(".md"):
        return True
    if rel.startswith("docs/") and rel.count("/") == 1 and rel.endswith(".md"):
        return True
    if re.match(r"mem20[a-z0-9_]*z/README\.md$", rel):
        return True
    return False


def line_violates(line: str) -> bool:
    """True when a line presents a retired band as current.

    A line that names the band as history (a retirement marker) is exempt.
    """
    lowered = line.lower()
    if any(marker in lowered for marker in RETIREMENT_MARKERS):
        return False
    return bool(
        TOOL_CLAIM.search(line)
        or DOMAIN_CLAIM.search(line)
        or PAIR_CLAIM.search(line)
        or TABLE_TOOL_CLAIM.search(line)
    )


def scan(root: Path) -> tuple[list[str], list[str]]:
    """Return (scope, violations). Each violation is 'path:line: text'."""
    scope = [rel for rel in tracked_files(root) if in_scope(rel)]
    violations: list[str] = []
    for rel in scope:
        path = root / rel
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, start=1):
            if line_violates(line):
                violations.append("%s:%d: %s" % (rel, number, line.strip()))
    return scope, violations


def self_test() -> int:
    """Prove the patterns fire on a seeded 270/27 doc and pass on the live pin."""
    tools, domains = 311, 39
    seeded = [
        "The server exposes 270 tools across 27 domains.",
        "| Tool surface | **270 tools / 27 domains** |",
        "MCP tools | 268",
        "It registers 257 tools.",
        "The surface is 306 tools across 38 domains.",
    ]
    clean = [
        "The server exposes %d tools across %d domains." % (tools, domains),
        "The retired 270 / 27 pair is history.",
        "270 tools was the pre-temporal surface.",
        "| Tool surface | **%d tools / %d domains** |" % (tools, domains),
    ]
    failures = 0
    for line in seeded:
        if not line_violates(line):
            print("SELF-TEST FAIL: seeded line not caught: %s" % line, file=sys.stderr)
            failures += 1
    for line in clean:
        if line_violates(line):
            print("SELF-TEST FAIL: clean line flagged: %s" % line, file=sys.stderr)
            failures += 1
    if failures:
        return 1
    print("SELF-TEST OK: %d seeded line(s) caught, %d clean line(s) passed" % (len(seeded), len(clean)))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None, help="repo root (default: this checkout)")
    parser.add_argument("--list", action="store_true", help="print the in-scope files and exit")
    parser.add_argument("--self-test", action="store_true", help="run the pattern self-test and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    root = repo_root(args.root)
    tools, domains = live_pin(root)
    scope, violations = scan(root)

    if args.list:
        print("live pin: %d tools / %d domains" % (tools, domains))
        print("in scope: %d file(s)" % len(scope))
        try:
            for rel in scope:
                print("  %s" % rel)
        except BrokenPipeError:
            pass
        return 0

    print("live pin: %d tools / %d domains" % (tools, domains))
    print("scanned: %d live doc(s)" % len(scope))
    if violations:
        print("DOC-COUNT DRIFT (%d):" % len(violations), file=sys.stderr)
        for violation in violations:
            print("  - %s" % violation, file=sys.stderr)
        print(
            "\nA live doc carries a retired tool/domain band. Replace it with the "
            "live pin (%d tools / %d domains) or mark the line as history."
            % (tools, domains),
            file=sys.stderr,
        )
        return 1
    print("OK: no retired tool/domain band in any live doc")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
