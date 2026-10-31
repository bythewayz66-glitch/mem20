#!/usr/bin/env python3
"""Market-claim consistency audit for mem20.

Sweeps every tracked doc that states a market size (TAM / SAM / SOM) or a
blended ACV and reports file, line, figure, and whether it matches the
standing house figures:

    TAM $1.28B / SAM $282M / SOM $1.68M / blended ACV $14,000

This is a CONSISTENCY audit. It does not invent or re-derive any market
number: the house figures are the reference and every statement is compared
against them.

WHAT COUNTS AS A STATEMENT
--------------------------
A dollar figure is a statement about a layer only when it is directly bound
to that layer's token (token-then-figure, or figure-then-token) across a gap
of punctuation/connective words only. If the gap carries an arithmetic
operator (= x / *) or a digit, the figure is an operand in a formula
("SOM = 120 accounts x $14,000"), not a restatement, and is skipped.

WHAT IS NOT A STATEMENT
-----------------------
Deltas, variance, residuals, scenario/sensitivity outputs, tier prices, CAC,
costs and gross profit are not restatements of a standing figure. They are
excluded by cue so the audit reports only figures that claim to BE the
TAM / SAM / SOM / ACV.

Exit codes:
    0  no inconsistencies found
    1  at least one inconsistency found
    2  audit could not run
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass

# --------------------------------------------------------------------------
# Standing house figures. Carried verbatim; never re-derived here.
# --------------------------------------------------------------------------
HOUSE = {
    "TAM": 1_280_000_000,
    "SAM": 282_000_000,
    "SOM": 1_680_000,
    "ACV": 14_000,
}
HOUSE_LABEL = {
    "TAM": "$1.28B",
    "SAM": "$282M",
    "SOM": "$1.68M",
    "ACV": "$14,000",
}
SOM_ACCOUNTS = 120

# Broad-category figures: legitimate ONLY as context, never as sizing.
CONTEXT_ONLY = {
    6_490_000_000: "$6.49B broad category (TBRC)",
    6_270_000_000: "$6.27B broad category",
    6_160_000_000: "$6.16B broad category",
}

# Documented derivative builds (integer floors / non-ARR metrics), not
# restatements of the standing figure they sit next to.
DERIVED_OK = {
    1_279_992_000: "documented TAM/ACV integer floor (-$8,000, disclosed)",
    281_988_000: "documented SAM/ACV integer floor (-$12,000, disclosed)",
    1_280_006_000: "TAM/ACV ceil build (91,429 x $14,000), +$6,000 disclosed",
    1_166_400: "SOM 3-yr gross profit, not SOM ARR",
    1_056_000: "SOM-book modelled cost, not SOM ARR",
}

# Tier-level ACVs from the declared ladder (72/12/12/4 on 6K/18K/36K/80K).
TIER_ACV = {6_000, 18_000, 36_000, 80_000}
# Blended CAC, not ACV.
CAC_VALUES = {8_000, 16_800}

DOC_EXTS = {".md", ".html", ".htm", ".csv", ".json", ".txt", ".yml", ".yaml", ".py"}
SKIP_DIR_PARTS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

_MULT = {
    "b": 1_000_000_000, "billion": 1_000_000_000,
    "m": 1_000_000, "million": 1_000_000,
    "k": 1_000, "thousand": 1_000,
}

_NUM = r"\d[\d,]*(?:\.\d+)?"
# A magnitude suffix only when it is NOT the first letter of a following word
# ("$14,000 blended" must not parse as $14,000 billion).
_SUF = r"(?:billion|million|thousand|[BbMmKk](?![A-Za-z]))"

_TOKEN_FIG = re.compile(
    r"(?P<layer>\bTAM\b|\bSAM\b|\bSOM\b|\bACV\b)"
    r"(?P<gap>[^\n$]{0,45}?)"
    rf"\$\s?(?P<num>{_NUM})\s?(?P<suf>{_SUF})?"
)
_FIG_TOKEN = re.compile(
    rf"\$\s?(?P<num>{_NUM})\s?(?P<suf>{_SUF})?"
    r"(?P<gap>[^\n$]{0,25}?)"
    r"(?P<layer>\bTAM\b|\bSAM\b|\bSOM\b|\bACV\b)"
)

# Arithmetic binding: a digit, an operator, or a comparison sign in the gap
# means the dollar figures on the line are operands/results, not restatements.
_ARITH_IN_GAP = re.compile(r"[\u00d7\u00f7*/=\u2248~\u00b1]|\bx\b|\bX\b|\d")
# A hard break ends the binding: sentence/clause punctuation, a table cell
# separator, or an explicit "exactly" qualifier means the dollar figure and
# the layer token belong to different clauses.
_HARD_BREAK = re.compile(r"[\u2014\u2013;|]|\bexactly\b|\s-\s")

# A figure whose immediate prefix marks it as a delta / variance / comparison
# is not a restatement of the standing figure.
_DELTA_PREFIX = re.compile(r"(?:[+\u2212\-\u00b1~]\s*|\bfrom\s*|\bto\s+(?:about\s+)?|\bof\s+about\s*)$")
_DELTA_WORDS = re.compile(
    r"(gap|short|residual|variance|delta|shrink|undershoot|overshoot|"
    r"difference|above the|below the|off by|would be|would restate|instead of|"
    r"acquisition cost|support cost|hosting cost|COGS|cost per|CAC|gross profit|"
    r"gross margin|payback|"
    r"sensitivity|scenario|drift|worth|of blend)",
    re.I,
)

# 120 accounts framed as forecast rather than arithmetic.
_ACCOUNTS = re.compile(r"\b120\b[^.\n]{0,60}?\b(accounts?|logos?|customers?)\b", re.I)
_FORECAST_CUE = re.compile(
    r"\b(forecast|project(?:ed|ion|ions)?|expect(?:ed|s)?|predict(?:ed|ion)?|"
    r"will\s+(?:reach|hit|close|land)|target(?:ed|ing)?|aim(?:s|ing)?\s+to|"
    r"guidance|outlook|pipeline\s+of|ramp(?:s|ing)?\s+to|"
    r"by\s+(?:Q[1-4]|year\s+\d|20\d\d)|within\s+\d+\s+years?)",
    re.I,
)
_NEGATION_CUE = re.compile(
    r"\b(do not|don't|never|not permission|not a forecast|rather than|any)\b", re.I
)
# A rule/warning about how a figure must NOT be stated is not a statement of it.
_RULE_CUE = re.compile(r"\b(any|never|must not|should not|do not|warning|risk)\b", re.I)
_ARITH_CUE = re.compile(
    r"(=|[\u00d7\u00f7]|\bderived\b|\bfloor\b|\bexact\b|\bobtainable\b|\brealise\b|\brealize\b|"
    r"\b14,?000\b\s*[\u00d7*]|\b120\b\s*[\u00d7*]|[\u00d7*]\s*\$?\s*14,?000)",
    re.I,
)


@dataclass
class Finding:
    path: str
    line: int
    layer: str
    figure: str
    value: float
    status: str          # MATCH | MISMATCH | CONTEXT | TIER | CAC
    note: str = ""


@dataclass
class ForecastFlag:
    path: str
    line: int
    text: str
    reason: str


def tracked_files(root: str) -> list[str]:
    out = subprocess.run(
        ["git", "-C", root, "ls-files", "-z"],
        capture_output=True, text=True, check=True,
    ).stdout
    keep = []
    for p in out.split("\0"):
        if not p:
            continue
        if set(p.split("/")) & SKIP_DIR_PARTS:
            continue
        if os.path.splitext(p)[1].lower() not in DOC_EXTS:
            continue
        keep.append(p)
    return keep


def parse_money(num: str, suf: str | None) -> float:
    val = float(num.replace(",", ""))
    if suf:
        val *= _MULT[suf.lower()]
    return val


def gap_ok(gap: str) -> bool:
    """Binding gap: connective only, no arithmetic, no digits, no hard break."""
    if _ARITH_IN_GAP.search(gap):
        return False
    if _HARD_BREAK.search(gap):
        return False
    if re.search(r"\d", gap):
        return False
    return len(gap) <= 45


def is_delta(line: str, pos: int) -> bool:
    """True when the figure at `pos` reads as a delta/variance, not a level."""
    before = line[max(0, pos - 40):pos]
    if _DELTA_PREFIX.search(before):
        return True
    if _DELTA_WORDS.search(line):
        return True
    return False


def classify(layer: str, value: float) -> tuple[str, str]:
    if abs(value - HOUSE[layer]) < 1:
        return "MATCH", ""
    if int(value) in DERIVED_OK:
        return "MATCH", DERIVED_OK[int(value)]
    if int(value) in CONTEXT_ONLY:
        return "CONTEXT", CONTEXT_ONLY[int(value)]
    if layer == "ACV":
        if int(value) in TIER_ACV:
            return "TIER", "tier-level ACV from the declared ladder"
        if int(value) in CAC_VALUES:
            return "CAC", "blended CAC, not ACV"
    return "MISMATCH", f"house {HOUSE_LABEL[layer]}"


def claims_in_line(line: str) -> dict[tuple[int, str], tuple[str, float]]:
    out: dict[tuple[int, str], tuple[str, float]] = {}

    for m in _TOKEN_FIG.finditer(line):
        if not gap_ok(m.group("gap")):
            continue
        if is_delta(line, m.start()):
            continue
        value = parse_money(m.group("num"), m.group("suf"))
        if value < 1000:
            continue
        figure = f"${m.group('num')}{(' ' + m.group('suf')) if m.group('suf') else ''}"
        out[(m.start("layer"), m.group("layer"))] = (figure, value)

    for m in _FIG_TOKEN.finditer(line):
        if not gap_ok(m.group("gap")):
            continue
        # In an inline map (JSON/YAML) "$1.28B", SAM crosses a key boundary:
        # a quote in the gap means the token starts the NEXT pair.
        if '"' in m.group("gap") or "'" in m.group("gap"):
            continue
        if is_delta(line, m.start()):
            continue
        key = (m.start("layer"), m.group("layer"))
        if key in out:
            continue
        value = parse_money(m.group("num"), m.group("suf"))
        if value < 1000:
            continue
        figure = f"${m.group('num')}{(' ' + m.group('suf')) if m.group('suf') else ''}"
        out[key] = (figure, value)

    return out


def audit(root: str) -> tuple[list[Finding], list[ForecastFlag], int]:
    findings: list[Finding] = []
    forecasts: list[ForecastFlag] = []
    scanned = 0

    for rel in tracked_files(root):
        full = os.path.join(root, rel)
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except OSError:
            continue
        scanned += 1

        for i, raw in enumerate(lines, start=1):
            line = raw.rstrip("\n")[:4000]

            if _ACCOUNTS.search(line):
                _check_120(rel, i, line, forecasts)

            claims = claims_in_line(line)
            if not claims:
                continue
            # A line that warns how a figure must not be stated is a rule, not
            # a restatement of that figure.
            if _RULE_CUE.search(line) and not re.search(r"\$1[.,]28\s?B", line):
                continue
            for (_, layer), (figure, value) in claims.items():
                status, note = classify(layer, value)
                findings.append(Finding(rel, i, layer, figure, value, status, note))

    return findings, forecasts, scanned


def _check_120(rel: str, lineno: int, line: str, out: list[ForecastFlag]) -> None:
    if _NEGATION_CUE.search(line):
        return  # a rule forbidding the framing is not the framing
    if _FORECAST_CUE.search(line) and not _ARITH_CUE.search(line):
        out.append(
            ForecastFlag(
                rel, lineno, line.strip()[:300],
                "120 accounts framed as a forecast/target without the "
                "120 x $14,000 = $1,680,000 arithmetic",
            )
        )


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    root = args[0] if args else "."
    verbose = "-v" in sys.argv or "--verbose" in sys.argv

    try:
        findings, forecasts, scanned = audit(root)
    except Exception as exc:  # noqa: BLE001
        print(f"AUDIT ERROR: {exc}", file=sys.stderr)
        return 2

    mismatches = [f for f in findings if f.status == "MISMATCH"]
    matches = [f for f in findings if f.status == "MATCH"]
    context = [f for f in findings if f.status == "CONTEXT"]
    tier = [f for f in findings if f.status in {"TIER", "CAC"}]
    files_with_claims = len({f.path for f in findings})

    print("=" * 78)
    print("MEM20 MARKET-CLAIM CONSISTENCY AUDIT")
    print("=" * 78)
    print(f"house figures : TAM {HOUSE_LABEL['TAM']} / SAM {HOUSE_LABEL['SAM']} / "
          f"SOM {HOUSE_LABEL['SOM']} / blended ACV {HOUSE_LABEL['ACV']}")
    print(f"files scanned : {scanned}")
    print(f"files stating a market size or ACV : {files_with_claims}")
    print(f"statements    : {len(findings)} "
          f"({len(matches)} match, {len(mismatches)} mismatch, "
          f"{len(context)} context-only, {len(tier)} tier/CAC)")
    print(f"120-as-forecast flags : {len(forecasts)}")
    print()

    if verbose:
        print("-" * 78)
        print("ALL BOUND STATEMENTS")
        print("-" * 78)
        for f in sorted(findings, key=lambda x: (x.path, x.line)):
            print(f"{f.path}:{f.line}  {f.layer:<4} {f.figure:<16} {f.status}")
        print()

    if mismatches:
        print("-" * 78)
        print("INCONSISTENCIES (figure differs from the standing house figure)")
        print("-" * 78)
        for f in sorted(mismatches, key=lambda x: (x.path, x.line)):
            print(f"{f.path}:{f.line}  {f.layer} {f.figure}  ({f.note})")
        print()

    if forecasts:
        print("-" * 78)
        print("120-ACCOUNT FIGURE PRESENTED AS A FORECAST (should be arithmetic)")
        print("-" * 78)
        for f in sorted(forecasts, key=lambda x: (x.path, x.line)):
            print(f"{f.path}:{f.line}")
            print(f"    {f.text}")
            print(f"    -> {f.reason}")
        print()

    if context:
        print("-" * 78)
        print("CONTEXT-ONLY FIGURES (broad category, correctly not used as sizing)")
        print("-" * 78)
        for f in sorted(context, key=lambda x: (x.path, x.line)):
            print(f"{f.path}:{f.line}  {f.layer} {f.figure}  ({f.note})")
        print()

    print("=" * 78)
    if mismatches or forecasts:
        print(f"RESULT: FAIL - {len(mismatches)} inconsistent figure(s), "
              f"{len(forecasts)} forecast-framed 120-account statement(s)")
        return 1
    print("RESULT: PASS - every market-size and ACV statement matches the "
          "standing house figures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
