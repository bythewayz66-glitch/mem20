#!/usr/bin/env python3
"""Tier-ladder sensitivity model for the $14,000 blended ACV.

The ladder in docs/finance/inputs.json was asserted to blend to $14,000 but was
never tested. This script tests it three ways the reconciliation note did not:

  1. PERCENTAGE SPACE  - does price x share/100 sum to $14,000?      (it does)
  2. INTEGER SPACE     - is that blend reachable on a 120-logo book? (it is not)
  3. DRIFT SPACE       - how many accounts of mix movement break it? (very few)

It writes docs/pricing/tier-sensitivity.csv. The document
docs/pricing/tier-sensitivity.md is then audited against that CSV by
docs/pricing/audit_acv_consistency.py, so no figure can be hand-transcribed.

House numbers are carried VERBATIM from docs/finance/inputs.json and are not
re-derived here.

Usage:  python3 docs/pricing/tier_sensitivity_model.py [--root .] [--write]
Exits 1 if any invariant fails.
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import sys
from math import comb

# ------------------------------------------------ carried verbatim, not derived
HOUSE_ACV = 14_000
TAM = 1_280_000_000
SAM = 282_000_000
SOM = 1_680_000
LOGOS = 120

HOSTING_PER_ACCOUNT = 1_880
TICKETS_PER_ACCOUNT = 24
COST_PER_TICKET = 100
DIRECT_SUPPORT = TICKETS_PER_ACCOUNT * COST_PER_TICKET       # $2,400
COGS_PER_ACCOUNT = HOSTING_PER_ACCOUNT + DIRECT_SUPPORT      # $4,280

# docs/finance/inputs.json -> tier_ladder (ACV, share of paying accounts)
LADDER = [("Team", 6_000, 0.72),
          ("Business", 18_000, 0.12),
          ("Scale", 36_000, 0.12),
          ("Enterprise", 80_000, 0.04)]

PRICES = [p for _, p, _ in LADDER]
SHARES = [s for _, _, s in LADDER]


def pct_blend() -> float:
    """Blend in percentage space: sum(price x share)."""
    return sum(price * share for _, price, share in LADDER)


def int_mix_from_shares(shares: list[float], logos: int = LOGOS) -> tuple[int, ...]:
    """Largest-remainder rounding of a share vector onto `logos` whole accounts.

    The only honest way to put a percentage mix on a real book: rounds to
    integers while preserving the total. Naive rounding of 86.4/14.4/14.4/4.8
    gives 86/14/14/5 which sums to 119, so a model that just round()s each tier
    silently loses an account.
    """
    raw = [s * logos for s in shares]
    base = [int(x) for x in raw]
    rem = logos - sum(base)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - base[i], reverse=True)
    for i in order[:rem]:
        base[i] += 1
    return tuple(base)


def naive_round(shares: list[float], logos: int = LOGOS) -> tuple[int, ...]:
    return tuple(round(s * logos) for s in shares)


def blend_of(mix: tuple[int, ...]) -> float:
    return sum(p * n for p, n in zip(PRICES, mix)) / sum(mix)


def exact_mixes(logos: int = LOGOS) -> list[tuple[int, ...]]:
    """Every non-negative integer mix of the four tiers summing to `logos` whose
    weighted mean is exactly HOUSE_ACV."""
    out = []
    for a in range(logos + 1):
        for b in range(logos - a + 1):
            for c in range(logos - a - b + 1):
                d = logos - a - b - c
                if 6_000 * a + 18_000 * b + 36_000 * c + 80_000 * d == HOUSE_ACV * logos:
                    out.append((a, b, c, d))
    return out


def total_mixes(logos: int = LOGOS, k: int = 4) -> int:
    """Stars and bars: C(logos + k - 1, k - 1)."""
    return comb(logos + k - 1, k - 1)


def som(blended: float, logos: int = LOGOS) -> dict:
    rev = blended * logos
    gp = (blended - COGS_PER_ACCOUNT) * logos
    return {"rev": rev, "gp": gp, "gp_per": blended - COGS_PER_ACCOUNT,
            "d_rev": rev - SOM, "d_rev_pct": (rev - SOM) / SOM * 100}


def wedges(base: tuple[int, ...], top_k: int = 12) -> list[dict]:
    """Move k accounts between two tiers. This is what a real quarter does."""
    rows = []
    for j in range(1, len(base)):
        for i, jj in ((0, j), (j, 0)):
            for k in range(1, top_k + 1):
                if base[i] - k < 0:
                    break
                m = list(base)
                m[i] -= k
                m[jj] += k
                rows.append({
                    "shift": f"{LADDER[i][0]}->{LADDER[jj][0]}", "k": k,
                    "mix": "/".join(map(str, m)),
                    "blend": blend_of(tuple(m)),
                })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    root = pathlib.Path(args.root).resolve()

    fails: list[str] = []

    # ---- 1. percentage space -------------------------------------------------
    pb = pct_blend()
    print("== 1. Percentage space ==")
    for tier, price, share in LADDER:
        print(f"  {tier:<11} ${price:>7,} x {share:>5.0%} = ${price * share:>10,.2f}")
    print(f"  {'blend':<11} {'':>8}   {'100%':>5} = ${pb:>10,.2f}")
    print(f"  delta vs house: ${pb - HOUSE_ACV:+,.2f}")
    if pb != HOUSE_ACV:
        fails.append(f"percentage blend is ${pb:,.2f}, not ${HOUSE_ACV:,}")

    # ---- 2. integer space ----------------------------------------------------
    lr = int_mix_from_shares(SHARES)
    nr = naive_round(SHARES)
    lr_blend = blend_of(lr)
    real = som(lr_blend)
    print("\n== 2. Integer space (the 120-logo book) ==")
    print(f"  share x 120      : {[round(s * LOGOS, 1) for s in SHARES]}  (sum {sum(s * LOGOS for s in SHARES):.0f})")
    print(f"  naive round()    : {list(nr)}  sum={sum(nr)}")
    print(f"  largest-remainder: {list(lr)}  sum={sum(lr)}  blend=${lr_blend:,.2f}")
    print(f"  reachable SOM    : ${real['rev']:,.2f}  vs house ${SOM:,} -> ${real['d_rev']:+,.2f} ({real['d_rev_pct']:+.2f}%)")
    print(f"  gross profit     : ${real['gp']:,.2f}  at GP/account ${real['gp_per']:,.2f}")

    # ---- 3. exact-mix solution set ------------------------------------------
    ex = exact_mixes()
    nearest = sorted(ex, key=lambda m: sum(abs(a - b) for a, b in zip(m, lr)))[0]
    l1 = sum(abs(a - b) for a, b in zip(nearest, lr))
    print("\n== 3. Exact-mix solution set ==")
    print(f"  total possible mixes at {LOGOS} logos, 4 tiers : {total_mixes():,}")
    print(f"  mixes landing exactly on ${HOUSE_ACV:,}      : {len(ex)}")
    print(f"  share of mix space                            : {len(ex) / total_mixes() * 100:.3f}%")
    print(f"  nearest exact mix to the declared one         : {list(nearest)} (L1={l1} accounts)")
    print(f"  that mix blends to                            : ${blend_of(nearest):,.2f}")

    # ---- 4. drift ------------------------------------------------------------
    print("\n== 4. Drift: one account of mix movement ==")
    steps = [p - PRICES[0] for p in PRICES[1:]]
    per_logo = [s / LOGOS for s in steps]
    for (tier, _, _), step, per in zip(LADDER[1:], steps, per_logo):
        print(f"  Team<->{tier:<10} step ${step:>6,} -> ${per:>8,.2f}/logo"
              f" | 1 account = {per / HOUSE_ACV * 100:>5.2f}% of blend"
              f" = ${per * LOGOS:>8,.0f} SOM"
              f" | $140 (1% SOM) = {140 / per:>6.2f} accounts")

    tol = []
    for band in (0.005, 0.01, 0.02, 0.05):
        per_dollar = band * HOUSE_ACV
        row = {"band_pct": band * 100, "blend_band": per_dollar, "som_band": per_dollar * LOGOS}
        for (tier, _, _), per in zip(LADDER[1:], per_logo):
            row[tier] = per_dollar / per
        tol.append(row)
        print(f"  within {band * 100:>4.1f}% of SOM (+-${per_dollar * LOGOS:>8,.0f}): "
              + "  ".join(f"{t}={row[t]:.2f}acct" for t, _, _ in LADDER[1:]))

    # ---- 5. two-way wedge table ---------------------------------------------
    wedge_rows = wedges(lr)
    print("\n== 5. Wedges off the reachable mix ==")
    for w in wedge_rows:
        print(f"  {w['shift']:<20} k={w['k']:>2}  blend=${w['blend']:>10,.2f}"
              f"  ({w['blend'] - HOUSE_ACV:+9,.2f})  SOM=${w['blend'] * LOGOS:>11,.0f}"
              f"  mix={w['mix']}")

    # ---- 6. mix sensitivity: 10 points of share -----------------------------
    print("\n== 6. Mix sensitivity: shift 10 points of share between tiers ==")
    ten = round(0.10 * LOGOS)
    m = list(lr); m[2] -= ten; m[3] += ten
    swap = blend_of(tuple(m))
    print(f"  {ten} accounts Scale->Enterprise: blend ${swap:,.2f} "
          f"({swap - HOUSE_ACV:+,.2f}), SOM ${swap * LOGOS:,.0f} "
          f"({swap * LOGOS - SOM:+,.0f} = {(swap * LOGOS - SOM) / SOM * 100:+.1f}%)")
    m2 = list(lr); m2[1] -= ten; m2[0] += ten
    swap2 = blend_of(tuple(m2))
    print(f"  {ten} accounts Business->Team   : blend ${swap2:,.2f} "
          f"({swap2 - HOUSE_ACV:+,.2f}), SOM ${swap2 * LOGOS:,.0f} "
          f"({swap2 * LOGOS - SOM:+,.0f} = {(swap2 * LOGOS - SOM) / SOM * 100:+.1f}%)")

    # ---- 7. price band -------------------------------------------------------
    print("\n== 7. +/-20% price band at the declared mix ==")
    bands = []
    for mult in (0.80, 0.90, 1.00, 1.10, 1.20):
        sc = [p * mult for p in PRICES]
        b = sum(p * s for p, s in zip(sc, SHARES))
        f = som(b)
        bands.append({"mult": mult, "blend": b, **f})
        print(f"  x{mult:.2f}  blend ${b:>9,.2f}  SOM ${f['rev']:>11,.0f}  "
              f"GP ${f['gp']:>11,.0f}  GP/acct ${f['gp_per']:>8,.2f}")

    # ---- 8. gross profit by tier (where the money actually is) --------------
    print("\n== 8. Gross profit by tier at the reachable mix ==")
    tier_rows = []
    tot_rev = tot_gp = 0
    for (tier, price, _), n in zip(LADDER, lr):
        rev = price * n
        gp_t = (price - COGS_PER_ACCOUNT) * n
        tot_rev += rev
        tot_gp += gp_t
        tier_rows.append({"tier": tier, "acv": price, "n": n, "rev": rev,
                          "gp_per": price - COGS_PER_ACCOUNT, "gp": gp_t,
                          "gm": (price - COGS_PER_ACCOUNT) / price * 100})
    for r in tier_rows:
        r["gp_share"] = r["gp"] / tot_gp * 100
        r["logo_share"] = r["n"] / LOGOS * 100
        r["leverage"] = r["gp_share"] / r["logo_share"]
        print(f"  {r['tier']:<11} ${r['acv']:>7,} x{r['n']:>3}  rev ${r['rev']:>9,}"
              f"  GP/account ${r['gp_per']:>8,}  GP ${r['gp']:>9,}"
              f"  GM {r['gm']:>5.1f}%  GPshare {r['gp_share']:>5.1f}%"
              f"  leverage {r['leverage']:>5.2f}x")
    print(f"  {'TOTAL':<11} {'':>8}  {LOGOS:>3}  rev ${tot_rev:>9,}"
          f"  {'':>12}  GP ${tot_gp:>9,}  GM {tot_gp / tot_rev * 100:>5.1f}%")

    team_gp = PRICES[0] - COGS_PER_ACCOUNT
    print(f"\n  replacement ratio (Team logos needed to replace 1 logo of another tier):")
    for (tier, price, _), n in zip(LADDER[1:], lr[1:]):
        print(f"    {tier:<11} {round((price - COGS_PER_ACCOUNT) / team_gp, 1):>6.1f} Team logos"
              f"   (replaces ${price:,} of ACV with ${round((price - COGS_PER_ACCOUNT) / team_gp) * PRICES[0]:,} of ACV)")

    # ---- write CSV ----------------------------------------------------------
    if args.write:
        out = root / "docs/pricing/tier-sensitivity.csv"
        with out.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["kind", "label", "k", "mix", "blended_acv_usd",
                        "delta_vs_house_usd", "som_revenue_usd", "som_gross_profit_usd"])
            for mix_row, label in ((lr, "declared largest-remainder"),
                                   (nearest, "nearest exact")):
                b = blend_of(mix_row)
                f = som(b)
                w.writerow(["mix", label, "", "/".join(map(str, mix_row)),
                            f"{b:.2f}", f"{b - HOUSE_ACV:.2f}",
                            f"{f['rev']:.2f}", f"{f['gp']:.2f}"])
            for wt in wedge_rows:
                f = som(wt["blend"])
                w.writerow(["wedge", wt["shift"], wt["k"], wt["mix"],
                            f"{wt['blend']:.2f}", f"{wt['blend'] - HOUSE_ACV:.2f}",
                            f"{f['rev']:.2f}", f"{f['gp']:.2f}"])
            for band in bands:
                w.writerow(["price_band", f"x{band['mult']:.2f}", "", "",
                            f"{band['blend']:.2f}", f"{band['blend'] - HOUSE_ACV:.2f}",
                            f"{band['rev']:.2f}", f"{band['gp']:.2f}"])
            for t in tol:
                w.writerow(["tolerance", f"{t['band_pct']:.1f}%", "", "",
                            f"{t['blend_band']:.2f}", "", f"{t['som_band']:.2f}", ""])
        print(f"\nwrote {out.relative_to(root)}")

    # ---- invariants ---------------------------------------------------------
    if sum(lr) != LOGOS:
        fails.append(f"largest-remainder mix sums to {sum(lr)}, not {LOGOS}")
    if LOGOS * HOUSE_ACV != SOM:
        fails.append(f"{LOGOS} x ${HOUSE_ACV:,} != ${SOM:,}")
    if round(SAM / HOUSE_ACV) != 20_143:
        fails.append("SAM/ACV cross-check drifted from 20,143")
    if round(TAM / HOUSE_ACV) != 91_429:
        fails.append("TAM/ACV cross-check drifted from 91,429")
    if PRICES != sorted(set(PRICES)):
        fails.append("tier prices are not strictly ascending")
    if [PRICES[i + 1] - PRICES[i] for i in range(3)] != [12_000, 18_000, 44_000]:
        fails.append("upgrade increments drifted from 12k/18k/44k")

    print()
    if fails:
        print("MODEL FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("MODEL OK - invariants hold. The ladder reconciles in percentage space")
    print(f"and is UNREACHABLE in integer space at {LOGOS} logos (${lr_blend:,.2f}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
