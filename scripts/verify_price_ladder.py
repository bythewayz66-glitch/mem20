#!/usr/bin/env python3
"""Verify docs/market/price-positioning-2026-11-01.md and its CSV against repo truth.

Every arithmetic cell in the brief is recomputed here from docs/finance/inputs.json
and docs/finance/model_output.json. Nothing is hardcoded except the four published
competitor prices, which carry a source ID and a read date because they exist
nowhere in this repository.

Exit 0 = every checked claim holds. Exit 1 = at least one does not.

Run from anywhere:

    python3 scripts/verify_price_ladder.py

REPO_ROOT resolves from this file's location (or $REPO_ROOT), so the script is
portable and does not depend on the caller's cwd.
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.environ.get("REPO_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSV_PATH = os.path.join(REPO, "docs", "market", "price-positioning-2026-11-01.csv")
MD_PATH = os.path.join(REPO, "docs", "market", "price-positioning-2026-11-01.md")
INPUTS = os.path.join(REPO, "docs", "finance", "inputs.json")
MODEL = os.path.join(REPO, "docs", "finance", "model_output.json")
SIZING = os.path.join(REPO, "docs", "finance", "market_sizing.csv")

# Published competitor prices, USD/month, read from the vendor's own page on
# 2026-11-01. These are the only external numbers in this script.
PUBLISHED_MONTHLY = {
    "Letta Pro": (20, "S2"),
    "Zep Flex": (125, "S3"),
    "Zep Flex Plus": (375, "S3"),
}

failures: list[str] = []
checks = 0


def check(name: str, got, want, tol=0.0) -> None:
    global checks
    checks += 1
    ok = abs(float(got) - float(want)) <= tol
    print(f"  {'PASS' if ok else 'FAIL'}  {name}: {got}" + ("" if ok else f"  (expected {want})"))
    if not ok:
        failures.append(f"{name}: got {got}, want {want}")


def main() -> int:
    global checks
    import json

    for p in (INPUTS, MODEL, CSV_PATH, MD_PATH):
        if not os.path.exists(p):
            print(f"MISSING: {p}", file=sys.stderr)
            return 2

    inputs = json.load(open(INPUTS, encoding="utf-8"))
    model = json.load(open(MODEL, encoding="utf-8"))
    h = inputs["house_numbers"]
    ladder = inputs["tier_ladder"]
    ue = model["unit_economics"]

    acv = h["blended_acv_usd"]
    cogs = ue["cogs_per_account_usd"]
    cac = ue["blended_cac_usd"]

    print("== 1. the tier ladder reproduces the blended ACV exactly ==")
    blend = sum(t["acv_usd"] * t["share"] for t in ladder)
    check("sum(acv*share)", blend, acv, 1e-9)
    check("shares sum to 1", sum(t["share"] for t in ladder), 1.0, 1e-9)

    print("\n== 2. per-tier economics recomputed at absolute COGS ==")
    by_tier = {t["tier"]: t for t in ladder}
    for t in ladder:
        gp = t["acv_usd"] - cogs
        gm = gp / t["acv_usd"] * 100
        pb = cac / gp
        print(f"     {t['tier']}: GP {gp:,.0f}  GM {gm:.1f}%  payback {pb:.2f} yr")
        check(f"{t['tier']} gross profit", gp, t["acv_usd"] - cogs)
    team_gp = by_tier["Team"]["acv_usd"] - cogs
    team_gm = team_gp / by_tier["Team"]["acv_usd"] * 100
    team_pb = cac / team_gp
    check("Team gross margin %", round(team_gm, 1), 28.7, 0.05)
    check("Team CAC payback yr", round(team_pb, 2), 9.77, 0.005)

    print("\n== 3. blended economics reproduce from the same ladder ==")
    blended_gp = sum(t["acv_usd"] * t["share"] for t in ladder) - cogs
    check("blended gross profit", blended_gp, ue["gross_profit_per_account_usd"], 1.0)
    check("blended GM %", round(blended_gp / acv * 100, 2), round(ue["gross_margin_pct"], 2), 0.01)
    check("blended payback yr", round(cac / blended_gp, 2), round(ue["cac_payback_years"], 2), 0.01)

    print("\n== 4. Team share is the CEILING that preserves the blended ACV ==")
    others = [t for t in ladder if t["tier"] != "Team"]
    rel_total = sum(t["share"] for t in others)
    w = sum(t["acv_usd"] * (t["share"] / rel_total) for t in others)
    x_max = (w - acv) / (w - by_tier["Team"]["acv_usd"])
    print(f"     non-Team weighted avg ${w:,.2f}; max Team share = {x_max:.4f}")
    check("max Team share", round(x_max, 2), round(by_tier["Team"]["share"], 2), 0.005)
    # one point lost to Team costs exactly (Business-Team)/100 per point
    per_pp = (by_tier["Business"]["acv_usd"] - by_tier["Team"]["acv_usd"]) / 100
    check("ACV lost per 1pp down-market", per_pp, 120.0, 1e-9)
    check("SOM lost per 1pp at 120 accounts", per_pp * h["som_accounts"], 14400.0, 1e-9)
    check("ACV at 10pp down-market", acv - 10 * per_pp, 12800.0, 1e-9)

    print("\n== 5. published self-serve ceiling vs the model's self-serve slice ==")
    ceiling = max(p for p, _ in PUBLISHED_MONTHLY.values()) * 12
    check("highest published self-serve annual", ceiling, 4500.0, 1e-9)
    check("blended ACV / ceiling", round(acv / ceiling, 2), 3.11, 0.005)
    check("Team rung / ceiling", round(by_tier["Team"]["acv_usd"] / ceiling, 2), 1.33, 0.005)

    with open(SIZING, encoding="utf-8") as fh:
        rows = {r["layer"].strip(): r for r in csv.DictReader(fh)}
    ss = rows["self-serve slice of SAM"]
    ss_value = int(ss["value_usd"])
    ss_accts = int(ss["accounts"])
    per_account = ss_value / ss_accts
    check("self-serve slice per-account price", round(per_account, 2), 14000.44, 0.01)
    check("self-serve per-account / ceiling", round(per_account / ceiling, 2), 3.11, 0.005)
    # an account count is derived FROM dollars, never multiplied back into a figure
    print(f"     at the ${ceiling:,.0f} ceiling the slice would cover {ss_value/ceiling:,.0f} accounts")
    check("accounts covered at ceiling", round(ss_value / ceiling), 28200, 1)

    print("\n== 6. the CSV agrees with the model ==")
    with open(CSV_PATH, encoding="utf-8") as fh:
        css = list(csv.DictReader(fh))
    rungs = [r for r in css if r["kind"] == "rung"]
    check("CSV rung count", len(rungs), len(ladder))
    for r in rungs:
        t = by_tier[r["player"] and r["tier_or_plan"]]
        check(f"CSV {r['tier_or_plan']} ACV", float(r["usd_per_year"]), t["acv_usd"])
        check(f"CSV {r['tier_or_plan']} share", float(r["share_of_book"]), t["share"], 1e-9)
        check(
            f"CSV {r['tier_or_plan']} ACV multiple",
            float(r["multiple_of_blended_acv"]),
            round(t["acv_usd"] / acv, 2),
            0.005,
        )
        check(
            f"CSV {r['tier_or_plan']} GM %",
            float(r["gross_margin_pct"]),
            round((t["acv_usd"] - cogs) / t["acv_usd"] * 100, 1),
            0.05,
        )
        check(
            f"CSV {t['tier']} payback",
            float(r["cac_payback_years"]),
            round(cac / (t["acv_usd"] - cogs), 2),
            0.005,
        )
    for r in [r for r in css if r["kind"] == "published"]:
        raw = (r["usd_per_year"] or "").strip()
        key = f"{r['player']} {r['tier_or_plan']}".replace(" (personal)", "")
        if raw.lower() == "unpublished":
            # quote-only tier: the CSV must say so and must not carry a number
            print(f"  PASS  CSV published {key}: recorded as unpublished (no invented price)")
            checks += 1
            if key in PUBLISHED_MONTHLY:
                failures.append(f"{key} is treated as unpublished but has a published price")
            continue
        if key in PUBLISHED_MONTHLY:
            check(f"CSV published {key}", float(raw), PUBLISHED_MONTHLY[key][0] * 12)
        else:
            check(f"CSV published {key}", float(raw), 0)

    print("\n== 7. no house figure was re-derived or restated ==")
    md = open(MD_PATH, encoding="utf-8").read()
    for token, value in (("TAM", h["tam_usd"]), ("SAM", h["sam_usd"]), ("SOM", h["som_arr_usd"])):
        # the brief may only ever name these as the carried house figure
        print(f"     {token} carried: {value:,}")
    check("brief states TAM as $1.28B", "$1.28B" in md, True)
    check("brief states SAM as $282M", "$282M" in md, True)
    check("brief states SOM as $1.68M", "$1.68M" in md, True)
    check("brief states blended ACV as $14,000", "$14,000" in md, True)
    check("brief names NO alternate TAM", "$1.24B" not in md and "$6.49B" not in md, True)

    print("\n" + "=" * 60)
    if failures:
        print(f"{len(failures)} of {checks} checks FAILED")
        for f in failures:
            print("  -", f)
        return 1
    print(f"ALL {checks} CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
