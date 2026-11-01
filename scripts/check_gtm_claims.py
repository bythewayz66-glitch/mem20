#!/usr/bin/env python3
"""Static claim gate over the go-to-market collateral in ``docs/gtm/``.

Why this exists
---------------
The GTM directory is the git-side source of truth for launch copy, and the copy
is read by people who will test what it says. Four classes of statement have
historically gone wrong there and each one is cheap to detect mechanically:

1. ``RETIRED_TOOL_COUNT`` - 257 / 258 / 268 (and the 26-domain figure) presented
   as the *current* surface. These are retired; they survive only as stated
   history. The surface of record is whatever CI pins, not a number in prose.
2. ``SITES_URL`` - a ``/sites/`` or ``/files/`` artifact URL used as a link or
   asset destination. Those URLs are project-member-only and return 403 to an
   anonymous visitor, so a launch link that points at one is a dead end.
3. ``PYPI_INSTALL`` - an install path that does not exist. The packages are not
   published; install is source-only.
4. ``UNLEDGERED_PERF_FIGURE`` - a performance number that does not appear in
   ``docs/gtm/claim-ledger.md``. If it is not in the ledger it has no provenance.

Design choices worth knowing before editing
-------------------------------------------
* **The expected tool surface is read from CI, never hardcoded here.** A gate
  that pins a number in a second place starts drifting the moment the first
  place moves - which is exactly the failure this gate is meant to catch.
* **Exemptions are line-local and explicit.** Retired numbers are legal on a
  line that *names* them as retired, banned, withdrawn or historical. The gate
  asks "is this presented as current?" and the only machine-checkable proxy for
  "presented as current" is the absence of a retirement marker on the same line.
  Keeping the markers line-local means every exemption is auditable by eye.
* **Ownership decides the exit code, not the report.** ``--scope all`` prints
  every violation in the directory including files owned by other seats, but
  only violations inside files this gate owns fail the run. Debt that belongs to
  another owner is reported as an attributed follow-up, so the gate can be
  adopted in CI today instead of waiting for that debt to clear.

Usage
-----
    python3 scripts/check_gtm_claims.py              # owned files only (gate)
    python3 scripts/check_gtm_claims.py --scope all  # whole directory (audit)
    python3 scripts/check_gtm_claims.py --strict     # exit 1 on any violation

Exit codes: 0 = no violation in scope, 1 = violation(s), 2 = cannot run.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Files this gate is responsible for. Everything else in docs/gtm/ is owned by
# another seat; violations there are reported, never used to fail this run.
OWNED_FILES = frozenset(
    {
        "docs/gtm/utm-registry.csv",
        "docs/gtm/launch-instrumentation.md",
        "scripts/check_gtm_claims.py",
    }
)

# Owner attribution for files we do not own, so an audit produces a routing
# table instead of an undifferentiated wall of violations.
KNOWN_OWNERS = {
    "docs/gtm/mem20-launch-copy.md": "Mem20 Content Creator (branch content/ws3-launch-copy-270)",
    "docs/gtm/claim-ledger.md": "mem20 GTM Team Lead (branch docs/ws1-gtm-claim-ledger-refresh)",
    "docs/gtm/mem20-campaign-plan.md": "mem20 GTM Team Lead",
    "docs/gtm/mem20-sales-one-pager.md": "mem20 GTM Team Lead",
    "docs/gtm/launch-channels-2026-11-01.md": "Launch Channels seat",
    "docs/gtm/launch-channels-evidence-2026-11-01.md": "Launch Channels seat",
    "docs/gtm/README.md": "mem20 GTM Team Lead",
}

RETIRED_TOOL_COUNTS = ("257", "258", "268")
RETIRED_DOMAIN_COUNTS = ("26",)

# A line carrying any of these is *talking about* a retired value rather than
# asserting it. Matched case-insensitively against the whole line.
RETIREMENT_MARKERS = (
    "retired",
    "banned",
    "withdrawn",
    "superseded",
    "previously",
    "previous_",
    "no longer",
    "was never",
    "never the total",
    "wrong prior",
    "wrong in two ways",
    "older",
    "historical",
    "do not report",
    "must not",
    "survive only",
    "only in",
    "~~",
    "differs from",
    "not comparable",
)

# A /sites/ URL on a line carrying one of these is evidence *about* the 403
# behaviour, not a destination being published.
EVIDENCE_MARKERS = (
    "403",
    "anonymous",
    "unreachable",
    "dead end",
    "not reachable",
    "member-only",
    "evidence",
    "forbidden",
    "cannot be sent",
    "never publish",
    "do not",
    "must not",
    "no launch asset",
    "URL:",
)

# The defect is a *published-package* install path, not pip itself. A source
# install (``pip install -r requirements.txt``, ``pip install -e ./mem20api``,
# ``pip install .``) is the documented and correct path, so it must not fire.
PYPI_MARKERS = (
    "pip install mem20",
    "pip3 install mem20",
    "pipx install mem20",
    "uv pip install mem20",
    "available on pypi",
    "published on pypi",
    "installable from pypi",
    "install from pypi",
    "from pypi:",
)

PYPI_NEGATION = (
    "not on pypi",
    "no pypi",
    "not published",
    "404",
    "source-only",
    "source only",
    "is not",
    "unavailable",
    "never",
    "do not",
    "must not",
    "without pypi",
    "banned",
    "not a gate",
    "nice to have",
)

SITES_URL_RE = re.compile(r"(?:https?://)?[A-Za-z0-9._-]*team?ily\.ai/sites/\S+|/sites/[A-Za-z0-9._-]+")
FILES_URL_RE = re.compile(r"(?:https?://)?[A-Za-z0-9._-]*teamily\.ai/files/\S+")

# Performance-shaped tokens, matched with their unit so that a rate and a
# latency can never be compared to each other. Each match yields a normalised
# key: rates keep 3+ decimals, latencies keep the ``ms`` suffix.
PERF_TOKEN_RE = re.compile(
    r"(?P<rate>\b0\.\d{3,6}\b)"
    r"|(?P<lat>\b\d{1,4}\.\d{1,2}\s?ms\b)"
    r"|(?P<pct>\b\d{1,3}\.\d{1,2}\s?%)",
    re.IGNORECASE,
)


def perf_key(token: str) -> str:
    """Normalise a performance token so units are part of the identity."""
    return token.replace(" ", "").lower()


CAVEAT_MARKERS = (
    "not comparable",
    "caveat",
    "retired",
    "withdrawn",
    "does not",
    "do not",
    "no claim",
    "unstandardised",
    "unstandardized",
    "denominator",
    "adversarial",
    "visible",
    "ledger",
    "provenance",
    "source:",
    "`latest.md`",
    "benchmarks/",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def surface_of_record(root: Path) -> tuple[str | None, str]:
    """Read the tool-surface number CI pins. Return (value, provenance)."""
    workflow = root / ".github" / "workflows" / "mcp-verify.yml"
    if not workflow.is_file():
        return None, "no .github/workflows/mcp-verify.yml"
    text = workflow.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"MEM20_EXPECTED_TOOLS:\s*\"?'?(\d+)", text)
    if not match:
        return None, "mcp-verify.yml has no MEM20_EXPECTED_TOOLS pin"
    return match.group(1), "MEM20_EXPECTED_TOOLS in .github/workflows/mcp-verify.yml"


def ledger_numbers(root: Path) -> set[str]:
    ledger = root / "docs" / "gtm" / "claim-ledger.md"
    if not ledger.is_file():
        return set()
    text = ledger.read_text(encoding="utf-8", errors="replace")
    return {m.group(0).replace(" ", "") for m in PERF_TOKEN_RE.finditer(text)}


def has_marker(line: str, markers: tuple[str, ...]) -> bool:
    low = line.lower()
    return any(m.lower() in low for m in markers)


def scan(root: Path, paths: list[Path], ledger: set[str]) -> list[dict]:
    violations: list[dict] = []
    for path in paths:
        rel = path.relative_to(root).as_posix()
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:  # pragma: no cover - unreadable file
            violations.append(
                {"file": rel, "line": 0, "rule": "UNREADABLE", "detail": str(exc)}
            )
            continue
        for number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("<!--"):
                continue

            # 1. retired counts asserted as current
            if not has_marker(line, RETIREMENT_MARKERS):
                for needle in RETIRED_TOOL_COUNTS:
                    if re.search(rf"\b{needle}\b\s*(?:tools|tool)", line, re.IGNORECASE):
                        violations.append(
                            {
                                "file": rel,
                                "line": number,
                                "rule": "RETIRED_TOOL_COUNT",
                                "detail": f"{needle} presented as the current tool surface",
                            }
                        )
                        break
                else:
                    for needle in RETIRED_DOMAIN_COUNTS:
                        if re.search(rf"\b{needle}\b\s*domains?", line, re.IGNORECASE):
                            violations.append(
                                {
                                    "file": rel,
                                    "line": number,
                                    "rule": "RETIRED_TOOL_COUNT",
                                    "detail": f"{needle} domains presented as the current surface",
                                }
                            )
                            break

            # 2. /sites/ (or /files/) artifact used as a destination
            for pattern, kind in ((SITES_URL_RE, "/sites/"), (FILES_URL_RE, "/files/")):
                for match in pattern.finditer(line):
                    if has_marker(line, EVIDENCE_MARKERS):
                        violations.append(
                            {
                                "file": rel,
                                "line": number,
                                "rule": "SITES_URL_EVIDENCE",
                                "detail": f"{kind} URL quoted as evidence: {match.group(0)[:80]}",
                            }
                        )
                    else:
                        violations.append(
                            {
                                "file": rel,
                                "line": number,
                                "rule": "SITES_URL",
                                "detail": f"{kind} URL used as a destination: {match.group(0)[:80]}",
                            }
                        )

            # 3. install path that does not exist
            if has_marker(line, PYPI_MARKERS) and not has_marker(line, PYPI_NEGATION):
                violations.append(
                    {
                        "file": rel,
                        "line": number,
                        "rule": "PYPI_INSTALL",
                        "detail": "install path implies a published package",
                    }
                )

            # 4. performance figure with no ledger provenance
            if not has_marker(line, CAVEAT_MARKERS):
                for match in PERF_TOKEN_RE.finditer(line):
                    token = match.group(0).replace(" ", "")
                    if token.lower() in {t.lower() for t in ledger}:
                        continue
                    violations.append(
                        {
                            "file": rel,
                            "line": number,
                            "rule": "UNLEDGERED_PERF_FIGURE",
                            "detail": f"{token!r} absent from docs/gtm/claim-ledger.md",
                        }
                    )
                    break

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--scope",
        choices=("owned", "all"),
        default="owned",
        help="'owned' gates only this gate's files; 'all' audits every docs/gtm/*.md",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail on violations in files owned by another seat as well",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    gtm = root / "docs" / "gtm"
    if not gtm.is_dir():
        print("ERROR: docs/gtm/ not found; run from a checkout of mem20", file=sys.stderr)
        return 2

    paths = sorted(gtm.glob("*.md"))
    if not paths:
        print("ERROR: no markdown files under docs/gtm/", file=sys.stderr)
        return 2

    pin, provenance = surface_of_record(root)
    ledger = ledger_numbers(root)

    owned_paths = [p for p in paths if p.relative_to(root).as_posix() in OWNED_FILES]
    scanned = paths if args.scope == "all" else owned_paths
    violations = scan(root, scanned, ledger)

    print("check_gtm_claims.py")
    print(f"  scope                : {args.scope} ({len(scanned)} file(s) scanned)")
    print(f"  surface of record    : {pin or 'UNKNOWN'} <- {provenance}")
    print(f"  ledger figure tokens : {len(ledger)}")
    print()

    hard = [v for v in violations if v["rule"] != "SITES_URL_EVIDENCE"]
    evidence = [v for v in violations if v["rule"] == "SITES_URL_EVIDENCE"]

    for v in hard:
        print(f"  [VIOLATION] {v['file']}:{v['line']}  {v['rule']}  {v['detail']}")

    if evidence:
        print(f"  ({len(evidence)} /sites/ URL(s) quoted as 403 evidence - recorded, not failed)")
        for v in evidence:
            print(f"    [evidence] {v['file']}:{v['line']}  {v['detail']}")

    owned_hard = [v for v in hard if v["file"] in OWNED_FILES]
    foreign_hard = [v for v in hard if v["file"] not in OWNED_FILES]

    if foreign_hard:
        print()
        print(f"  ATTRIBUTED FOLLOW-UPS - {len(foreign_hard)} violation(s) in files owned by other seats:")
        by_file: dict[str, list[dict]] = {}
        for v in foreign_hard:
            by_file.setdefault(v["file"], []).append(v)
        for file in sorted(by_file):
            owner = KNOWN_OWNERS.get(file, "unassigned in KNOWN_OWNERS")
            lines = ", ".join(str(v["line"]) for v in by_file[file])
            rules = sorted({v["rule"] for v in by_file[file]})
            print(f"    {file}  ({len(by_file[file])} hit(s); lines {lines})")
            print(f"      owner : {owner}")
            print(f"      rules : {', '.join(rules)}")

    print()
    print(f"  summary: {len(hard)} violation(s), {len(evidence)} evidence record(s), "
          f"{len(scanned)} file(s) in scope")
    print(f"  owned : {len(owned_hard)} violation(s)")
    print(f"  others: {len(foreign_hard)} violation(s)")

    failing = owned_hard if not args.strict else hard
    if failing:
        print("  RESULT: FAIL")
        return 1
    print("  RESULT: PASS" + (" (foreign debt reported above)" if foreign_hard else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
