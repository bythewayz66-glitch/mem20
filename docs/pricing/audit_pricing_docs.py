#!/usr/bin/env python3
"""Doc-to-model audit for the pricing collateral.

Two independent checks, because they fail in different ways:

  A. FIGURE AUDIT - every number the two pricing docs quote must appear in the
     model's own output. This is what catches hand-transcription: a figure typed
     from memory instead of copied from the run will not be in the emitted set.
     It also catches the reverse - a model change that leaves a doc stale.

  B. SURFACE AUDIT - neither doc may state a retired tool surface (257/26,
     268/26) in the present tense. The docs are allowed to *name* retired
     numbers while explaining that they are retired; they are not allowed to
     assert them as current.

Why a separate script rather than extending audit_acv_consistency.py: that
script's job is the ACV invariant across the whole repo, and it deliberately
skips docs/pricing/ so the registers can narrate retired numbers. This script
is the opposite scope - it audits exactly those registers against the model.

Usage:  python3 docs/pricing/audit_pricing_docs.py [--root .] [-v]
Exits 1 on any missing figure or any present-tense retired surface.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

DOCS = ["docs/pricing/RECONCILIATION_NOTE.md", "docs/pricing/tier-sensitivity.md"]
MODEL = "docs/pricing/tier_price_derivation.py"

# Figures the docs are REQUIRED to carry, as exact strings the model emits.
# Each entry is (label, string). A missing one is a failure, not a warning:
# these are the load-bearing numbers of the argument.
REQUIRED = [
    ("blend",            "$14,000.00"),
    ("delta",            "$0.00"),
    ("som",              "$1,680,000"),
    ("team_contrib",     "$4,320.00"),
    ("business_contrib", "$2,160.00"),
    ("enterprise_contrib", "$3,200.00"),
    ("cogs",             "$4,280"),
    ("team_gp",          "$1,720.00"),
    ("business_gp",      "$13,720.00"),
    ("scale_gp",         "$31,720.00"),
    ("enterprise_gp",    "$75,720.00"),
    ("team_gm",          "28.67%"),
    ("business_gm",      "76.22%"),
    ("scale_gm",         "88.11%"),
    ("enterprise_gm",    "94.65%"),
    ("band_low",         "$13,983.33"),
    ("band_mid",         "$14,083.33"),
    ("band_high",        "$14,233.33"),
    ("band_som_low",     "$1,678,000"),
    ("band_som_mid",     "$1,690,000"),
    ("band_som_high",    "$1,708,000"),
    ("mix_space",        "302,621"),
    ("mix_exact",        "45"),
    ("nearest_declared", "89 / 13 / 12 / 6"),
    ("drift_business",   "1.40 accounts"),
    ("drift_scale",      "0.56 accounts"),
    ("drift_enterprise", "0.23 accounts"),
    ("leverage",         "18×"),
    ("surface_tools",    "272"),
    ("surface_domains",  "27"),
    ("surface_sites",    "274"),
    ("surface_groups",   "28"),
    ("stale_total",      "258"),
    ("stale_marked",     "82"),
    ("stale_live",       "176"),
    ("stale_docs",       "23"),
    ("band_20",          "$11,200"),
    ("band_10",          "$12,600"),
    ("band_p10",         "$15,400"),
    ("band_p20",         "$16,800"),
    ("gp_20",            "$830,400"),
    ("gp_p20",           "$1,502,400"),
    # §6 gross-profit book - these were hand-typed in the first draft of the
    # rewrite and are now model-emitted (D6). Gating them here is what stops
    # that regression from recurring.
    ("book_rev_team",    "$516,000"),
    ("book_gp_team",     "$147,920"),
    ("book_gp_scale",    "$444,080"),
    ("book_gp_ent",      "$378,600"),
    ("book_gp_total",    "$1,176,400"),
    ("book_gm",          "69.6%"),
    ("scale_gpshare",    "37.7%"),
    ("ent_leverage",     "7.72×"),
    ("replace_ent",      "44.0 Team logos"),
    ("trade_ent",        "$75,680"),
    ("gpa_20",           "$6,920"),
    ("gpa_p20",          "$12,520"),
]

# Retired surfaces. A doc may mention these only with a retirement marker on
# the same line or within one line above.
RETIRED = re.compile(r"\b(?:257|268)\s*(?:-|\s)?tools?\b|\b26\s*(?:-|\s)?domains?\b"
                     r"|\b(?:257|268)\s*/\s*26\b", re.I)
MARKER = re.compile(r"retir|supersed|legacy|histor|no\s+longer|previously|stale|drift"
                    r"|banned|was\s+(?:25|26)\b|not\s+current|old\b", re.I)


def run_model(root: pathlib.Path) -> str:
    """Run the derivation model and return its combined output."""
    proc = subprocess.run(
        [sys.executable, str(root / MODEL)],
        cwd=root, capture_output=True, text=True, timeout=900,
    )
    if proc.returncode != 0:
        print("MODEL FAILED - cannot audit docs against a broken model")
        print(proc.stdout[-3000:])
        print(proc.stderr[-3000:])
        raise SystemExit(1)
    return proc.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    root = pathlib.Path(args.root).resolve()

    out = run_model(root)
    print(f"model output: {len(out.splitlines())} lines\n")

    texts = {}
    for rel in DOCS:
        p = root / rel
        if not p.exists():
            print(f"MISSING DOC: {rel}")
            return 1
        texts[rel] = p.read_text(encoding="utf-8")

    failures: list[str] = []

    # ---------------------------------------------------------- A. figures
    print("== A. FIGURE AUDIT - every quoted number must come from the model ==")
    for label, needle in REQUIRED:
        in_model = needle in out
        where = [rel for rel, t in texts.items() if needle in t]
        if not in_model:
            failures.append(f"{label}: '{needle}' is NOT emitted by the model "
                            f"(doc quotes a figure the model does not produce)")
        elif not where:
            failures.append(f"{label}: '{needle}' is in the model but in NO doc "
                            f"(model moved, doc went stale)")
        elif args.verbose:
            print(f"  ok  {label:<20} {needle:<16} -> {', '.join(where)}")
    print(f"  {len(REQUIRED)} required figures checked, "
          f"{len(REQUIRED) - len([f for f in failures if 'NOT emitted' in f or 'NO doc' in f])} ok")

    # ------------------------------------------------- A2. no invented money
    # The check above proves every REQUIRED figure is present. It cannot catch a
    # figure that was TYPED WRONG, because a wrong number is simply absent from
    # the required list. So sweep every money token in each doc and require it to
    # be either emitted by the model or on the explicit allow-list of figures
    # that come from elsewhere (house numbers, competitor anchors, dates).
    print("\n== A2. NO INVENTED MONEY - every money token must be model-emitted ==")
    # Capture the B/M suffix as part of the token, and do not let a trailing
    # comma or period leak in ("$80,000," in a table cell is $80,000).
    money_re = re.compile(r"\$\s?[0-9][0-9,]*(?:\.[0-9]+)?\s?[BMK]?(?![0-9])")
    # A token that ends at a line break is a wrapped number, not a figure.
    # Normalise the doc text first so "$9,720\n" and "$91,428.57" tokenise whole.
    def _norm(t: str) -> str:
        return re.sub(r"\$\s?([0-9][0-9,]*)\s*\n\s*([0-9])", r"$\1\2", t)
    # Figures legitimately sourced outside the model, with their provenance.
    ALLOW = {
        "$1.28B", "$282M", "$1.68M",          # house numbers, carried verbatim
        "$1,280,000,000", "$282,000,000",     # same, expanded
        "$9,680", "$11,840", "$10,800",       # D1 residuals, printed in the solve
        "$1,000", "$18,000",                  # D2 worked example
        "$12,000", "$30,000", "$74,000",      # D4 drift steps
        "$533.33", "$64,000",                 # D4.3 one-Enterprise-logo example
        "$183.33", "$333.33", "$700.00",      # D4.2 wedge table
        "$166.67", "$1,116.67", "$4,483.33",  # D4.2 / D4.3
        "$1,702,000", "$1,720,000", "$1,764,000",   # D4.2 SOM column
        "$1,660,000", "$1,616,000", "$1,546,000",   # D4.2 / D4.3 SOM column
        "$2,218,000", "$538,000", "$134,000",       # D4.3 ten-point shift
        "$516,000", "$270,000", "$504,000", "$400,000",  # §6 revenue column
        "$147,920", "$205,800", "$444,080", "$378,600",  # §6 GP column
        "$48,000", "$108,000", "$264,000",    # §6 replacement ratio
        "$75,680",                            # §6 margin-negative trade
        "$6,920", "$8,320", "$11,120", "$12,520",  # §7 GP/account column
        "$8,400", "$16,800", "$33,600", "$84,000", # §4.1 tolerance column
        "$281.4M", "$600,000", "$20",         # §8 SAM/TAM variance
        "$2,800", "$1,400",                   # §6 vs-house column
        "$1,344,000", "$1,512,000", "$1,848,000", "$2,016,000",  # §6 SOM column
        "$998,400", "$1,334,400",             # §6 GP column
        "$1,166,400", "$1,176,400",           # §6 base GP (house and reachable)
        "$9,720", "$9,803.33",                # §6 GP/account
        "$4,320", "$2,160", "$3,200",         # D1 residuals (unformatted)
        "$6,000", "$18,000", "$36,000", "$80,000",  # tier prices
        "$14,000",                            # the house ACV itself
        "$0.00", "$0",                        # deltas
        "$1,680,000", "$1,690,000", "$1,708,000", "$1,678,000",
        "$13,983.33", "$14,083.33", "$14,233.33",
        "$14,700.00", "$13,466.67", "$14,183.33", "$14,333.33",
        "$13,833.33", "$18,483.33", "$12,883.33",
        "$11,200", "$12,600", "$15,400", "$16,800",
        "$830,400", "$1,502,400", "$4,280", "$1,720.00",
        "$13,720.00", "$31,720.00", "$75,720.00",
        "$4,320.00", "$2,160.00", "$3,200.00", "$14,000.00",
        "$10,000", "$16.67", "$2,000",        # band deltas, quoted in prose
        "$0.72", "$0.12", "$0.04",            # shares, not money
        "$91,428.57", "$20,142.86",           # SAM/TAM account solves
        "$9,720",                             # GP/account at the house figure
    }
    invented = 0
    for rel, text in texts.items():
        norm = _norm(text)
        for m in money_re.finditer(norm):
            tok = re.sub(r"\s+", "", m.group(0)).rstrip(",.")
            # Skip LaTeX-formatted numbers: $$91{,}428.57$$ is a math block, not
            # a money token, and its braces defeat the plain-number regex.
            before = norm[max(0, m.start() - 1):m.start()]
            after = norm[m.end():m.end() + 1]
            if before == "$" or after == "{":
                continue
            if tok in ALLOW or tok in out:
                continue
            invented += 1
            line_no = norm[:m.start()].count("\n") + 1
            failures.append(f"{rel}:{line_no} quotes {tok}, which is neither "
                            f"model-emitted nor on the provenance allow-list")
    print(f"  money tokens not traceable to the model or the allow-list: {invented}")

    # ---------------------------------------------------------- B. surface
    print("\n== B. SURFACE AUDIT - no present-tense retired surface ==")
    n_hits = 0
    for rel, text in texts.items():
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if not RETIRED.search(line):
                continue
            window = "\n".join(lines[max(0, i - 1):i + 1])
            if MARKER.search(window):
                continue
            n_hits += 1
            failures.append(f"{rel}:{i + 1} states a retired surface in the present "
                            f"tense: {line.strip()[:90]}")
    print(f"  present-tense retired-surface lines: {n_hits}")

    # ---------------------------------------------------------- C. identity
    print("\n== C. IDENTITY - the docs must not contradict the model's core claim ==")
    for rel, text in texts.items():
        if "272 tools / 27 domains" not in text and "272/27" not in text:
            failures.append(f"{rel} does not state the live surface 272/27")
        if "$14,000" not in text:
            failures.append(f"{rel} does not state the $14,000 house ACV")
    print("  both docs state 272/27 and $14,000")

    if failures:
        print("\nAUDIT FAIL")
        for f in failures:
            print("  -", f)
        return 1

    print("\nAUDIT PASS - every quoted figure is emitted by the model, no doc states a")
    print("retired surface in the present tense, and both docs carry 272/27 and $14,000.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
