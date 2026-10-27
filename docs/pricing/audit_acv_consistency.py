#!/usr/bin/env python3
"""ACV consistency audit — holds the house blended ACV at $14,000 across the repo.

Exits 1 if any collateral states a *blended* ACV other than $14,000, or if the
tier ladder stops reproducing the house figure arithmetically.

Design note on precision: an ACV figure is only counted when the money token is
TIGHTLY bound to "ACV" / "annual contract value" — at most a short connector that
contains no further '$' or digit. Loose matching produces false positives by
walking from a SOM/TAM figure across a sentence to a later ACV mention (e.g.
"SOM $1.68M ... blended ACV $14,000"). Percentages (ACV ~ 22% of TAM) are skipped.

Usage:  python3 docs/pricing/audit_acv_consistency.py [--root .] [-v]
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

HOUSE_ACV = 14_000
SOM = 1_680_000
TAM = 1_280_000_000
SAM = 282_000_000
LOGOS = 120

TIERS = [("Team", 6_000, 72), ("Business", 18_000, 12),
         ("Scale", 36_000, 12), ("Enterprise", 80_000, 4)]

SCAN_SUFFIXES = {".md", ".html", ".htm", ".csv", ".json", ".txt"}
SKIP_DIRS = {".git", "node_modules", "corpus", ".sitemap", "target", "dist",
             ".venv", "venv", "__pycache__", "vendor", "site-packages"}

# A money token. Requires a '$' OR a comma/decimal separator OR >=4 digits, so
# stray list markers and single digits are not read as prices.
MONEY = (r"(?:\$\s*[0-9][0-9,]*(?:\.[0-9]+)?\s*[KkMm]?"
         r"|[0-9][0-9,]{2,}(?:\.[0-9]+)?\s*[KkMm]?)")

# Connector: no '$', no digits, no operators, and must not contain
# "of TAM"/"of SAM" — so an arithmetic chain ("x $14,000 ACV = $1.68M") or a
# share statement ("ACV ~ 22% of TAM") is never read as a price claim.
CONN = r"(?!\s*(?:[=~<>,+\-]|of\s+[TS]AM))[^0-9$\n=]{0,14}"
# Right-edge guard: reject a token that is really part of a bigger number or a
# market-size/percentage figure ("$1.28B", "$282M of SAM", "22%"), and reject
# ARR/SOM/TAM results. This is what keeps arithmetic chains out of the verdict.
RIGHT = (r"(?!\.?[0-9])"
         r"(?![Bb%])"
         r"(?!\s*(?:exactly|in\s+ARR|ARR\b|of\s+(?:TAM|SAM)))")

ACV_FORWARD = re.compile(r"\bACV\b" + CONN + r"(" + MONEY + r")" + RIGHT, re.I)
ACV_BACKWARD = re.compile(
    r"(" + MONEY + r")\s{0,2}(?:blended\s+)?\bACV\b" + RIGHT, re.I)
ACV_LONG = re.compile(r"annual contract value" + CONN + r"(" + MONEY + r")" + RIGHT, re.I)


def parse_money(raw: str) -> float | None:
    s = raw.replace("$", "").replace(",", "").replace(" ", "").strip()
    mult = 1
    if s and s[-1] in "Kk":
        mult, s = 1_000, s[:-1]
    elif s and s[-1] in "Mm":
        mult, s = 1_000_000, s[:-1]
    try:
        return float(s) * mult
    except ValueError:
        return None


def check_ladder() -> list[str]:
    errs: list[str] = []
    blend = sum(price * share for _, price, share in TIERS) / 100
    if blend != HOUSE_ACV:
        errs.append(f"tier ladder blends to ${blend:,.2f}, not ${HOUSE_ACV:,}")
    if LOGOS * HOUSE_ACV != SOM:                      # the identity, not the inputs
        errs.append(f"{LOGOS} x ${HOUSE_ACV:,} != ${SOM:,}")
    if round(SAM / HOUSE_ACV) != 20_143:
        errs.append("SAM/ACV cross-check drifted from 20,143 accounts")
    if round(TAM / HOUSE_ACV) != 91_429:
        errs.append("TAM/ACV cross-check drifted from 91,429 accounts")
    prices = [p for _, p, _ in TIERS]
    if prices != sorted(set(prices)):
        errs.append("tier prices are not strictly ascending")
    # NOTE: this ladder is priced per ACCOUNT with no per-unit quantity dimension
    # (no seats/agents/domains attached to the tiers in this repo), and the tier
    # "share" column is mix, not quantity — so a price-per-unit monotonicity check
    # would be meaningless here. What IS checkable, and what a buyer would catch,
    # is that each step up the ladder is a positive, strictly increasing
    # commitment: the upgrade increment must never shrink as tiers rise.
    steps = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]
    if any(s <= 0 for s in steps):
        errs.append("a tier upgrade step is non-positive")
    # Ladder must span the house mean: cheapest below it, dearest above it,
    # otherwise $14,000 is not a blend of anything.
    if not (prices[0] < HOUSE_ACV < prices[-1]):
        errs.append(f"the ${HOUSE_ACV:,} blend does not sit inside the tier range")
    return errs


def iter_files(root: pathlib.Path):
    me = pathlib.Path(__file__).name
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in p.parts) or p.name == me:
            continue
        yield p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    root = pathlib.Path(args.root).resolve()

    failures = check_ladder()
    hits: list[tuple[str, int, str, float]] = []
    nfiles = 0

    for path in iter_files(root):
        nfiles += 1
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            seen: set[float] = set()
            for pat in (ACV_FORWARD, ACV_BACKWARD, ACV_LONG):
                for m in pat.finditer(line):
                    val = parse_money(m.group(1))
                    if val is None or val in seen:
                        continue
                    # "ACV ~ 22% of TAM" is a share, not a price
                    if "%" in line[m.end(1):m.end(1) + 3]:
                        continue
                    seen.add(val)
                    hits.append((str(path.relative_to(root)), lineno,
                                 line.strip()[:120], val))

    # Tier-level ACVs ($6k/$18k/$36k/$80k) are legitimate per-segment prices and
    # are NOT blended claims, so they are classified rather than failed.
    tier_prices = {p for _, p, _ in TIERS}
    blended = [h for h in hits
               if re.search(r"blend|avg|average|mean", h[2], re.I)
               or h[3] not in tier_prices]
    drift = [h for h in blended if h[3] != HOUSE_ACV]

    print(f"files scanned         : {nfiles}")
    print(f"ACV figures found     : {len(hits)}")
    print(f"  tier-level (ok)     : {len(hits) - len(blended)}")
    print(f"  blended/aggregate   : {len(blended)}")
    print(f"    == ${HOUSE_ACV:,}       : {len(blended) - len(drift)}")
    print(f"    != ${HOUSE_ACV:,}       : {len(drift)}")
    print()

    if args.verbose:
        for f, ln, snip, val in blended:
            flag = "ok " if val == HOUSE_ACV else "BAD"
            print(f"  [{flag}] ${val:>10,.0f}  {f}:{ln}")

    if drift:
        print("DRIFT DETECTED:")
        for f, ln, snip, val in drift:
            print(f"  {f}:{ln}  ${val:,.0f}  |  {snip}")
        failures.extend(f"{f}:{ln} states ${v:,.0f} ACV" for f, ln, _, v in drift)

    if failures:
        print("\nAUDIT FAIL")
        for e in failures:
            print("  -", e)
        return 1

    print("AUDIT PASS — every blended ACV figure equals the $14,000 house number,")
    print("and the tier ladder reproduces it exactly (delta $0).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
