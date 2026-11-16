#!/usr/bin/env python3
"""mem20 4.0 pricing model - packaging, willingness-to-pay, margin structure.

This is the pricing layer that sits ON TOP of ``compute_model.py``. It does not
re-derive the house numbers; it reads them from ``inputs.json`` and treats them
as invariants, exactly as the finance model does.

What it answers
---------------
1. PACKAGING   - what each 4.0 tier contains, what it is gated on, and what the
                 ladder blends to at the declared mix.
2. WTP         - what the market has actually published, where mem20 sits
                 against that ceiling, and what the governance capability is
                 worth by published-adjacent anchor.
3. MARGIN      - contribution per tier, gross-profit concentration, and the
                 quantified cost of bundling the governance moat into the
                 entry tier.
4. SENSITIVITY - a +/-20% price grid with volume response, revenue, gross
                 profit, win rate, and the break-even elasticity.

Two scenarios, deliberately
---------------------------
Scenario A is the **committed** ladder (72/12/12/4 on $6K/$18K/$36K/$80K). It
blends to exactly $14,000 and therefore leaves every house number untouched.
It is the baseline and it is what CI asserts.

Scenario B is the **proposed** 4.0 repackaging. It keeps the four list prices
and changes only what is gated into each tier, which moves the mix from
72/12/12/4 to 58/24/14/4 and the blend from $14,000 to $16,040. That moves a
house number, so it is reported as a delta and never written into
``inputs.json``. Adopting it is an owner decision, not a model decision.

Usage
-----
    python3 docs/finance/pricing_model_v4.py --check   # verify invariants only
    python3 docs/finance/pricing_model_v4.py           # verify + write artefacts

Exit codes: 0 = ok, 1 = invariant drift, 2 = cannot run.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INPUTS = os.path.join(HERE, "inputs.json")

# ---------------------------------------------------------------------------
# Invariants. These are house numbers. The model refuses to emit a drifted
# figure rather than quietly agreeing with itself.
# ---------------------------------------------------------------------------
HOUSE_ACV = 14000
HOUSE_SOM = 1680000
HOUSE_ACCOUNTS = 120
HOUSE_TAM = 1280000000
HOUSE_SAM = 282000000

# ---------------------------------------------------------------------------
# Published competitive price points, annualised, USD.
# Every row carries the source ID from docs/market/source-register-2026-11-01.md
# so a reader can re-check the claim. Only published prices are used; vendors
# that publish nothing are recorded as quote-only and are NOT given a number.
# ---------------------------------------------------------------------------
COMPETITOR_POINTS = [
    # (player, plan, usd_per_year, source_id, segment, note)
    #
    # segment="memory_api"  - a developer memory / agent-memory product. This is
    #                         the distribution mem20's Team tier actually competes
    #                         in, and it is the one that sets the category ceiling.
    # segment="substrate"   - a vector store / database. Adjacent, not a memory
    #                         product; kept for context, excluded from the ceiling.
    # segment="governance"  - an audit / control layer. A DIFFERENT budget line
    #                         from a memory API. Used only as the anchor for the
    #                         governance capability, never as a memory-API price.
    ("Mem0", "Hobby", 0, "S1", "memory_api", "free tier, 10k add / 1k retrieval per month"),
    ("Letta", "Pro (personal)", 240, "S2", "memory_api", "$20/seat/mo annualised"),
    ("Zep", "Flex", 1500, "S5", "memory_api", "$125/mo annualised"),
    ("Mem0", "Pro", 2988, "S2", "memory_api", "$249/mo annualised"),
    ("Zep", "Flex Plus", 4500, "S5", "memory_api", "$375/mo annualised"),
    ("Pinecone", "Standard (min)", 600, "S19", "substrate", "$50/mo minimum"),
    ("Weaviate", "Plus", 3360, "S23", "substrate", "$280/mo annualised"),
    ("Lyzr", "platform top tier", 11988, "S29", "governance", "$999/mo annualised"),
]

# Governance-adjacent anchor band: what a buyer already pays for an audit /
# control layer, as distinct from a memory API. This is the band the epistemic
# partition + provenance ledger + contamination audit competes in.
GOVERNANCE_ANCHOR_LOW = 11988   # Lyzr platform top tier, S29
GOVERNANCE_ANCHOR_HIGH = 12000  # rounded ceiling of the same published tier

# ---------------------------------------------------------------------------
# Analyst assumptions. Each one is labelled and each one is stress-tested in
# the sensitivity grid. None of these is a measured figure and none of them is
# allowed to move a house number.
# ---------------------------------------------------------------------------
ASSUMPTIONS = {
    "price_elasticity": {
        "value": -0.8,
        "basis": "analyst assumption for B2B developer infrastructure; "
                 "not measured on mem20. Stress-tested from -0.2 to -2.0.",
    },
    "cogs_flat_by_tier": {
        "value": True,
        "basis": "carried from compute_model.py: hosting $1,880 + support $2,400 "
                 "per account, not varied by tier. A tier-varying COGS would "
                 "raise Team margin and lower Enterprise margin.",
    },
    "support_tickets_per_account": {
        "value": 24,
        "basis": "declared in inputs.json acquisition_inputs.tickets_per_account",
    },
    "governance_attach_rate_baseline": {
        "value": 0.28,
        "basis": "analyst assumption: share of Team buyers who would pay for the "
                 "governance bundle if it were sold separately rather than bundled. "
                 "Stress-tested 0.15-0.45.",
    },
    "win_rate_at_list": {
        "value": 0.34,
        "basis": "analyst assumption for a category with no published mem20 win "
                 "data. Used only to shape the sensitivity curve, never to state "
                 "an actual win rate.",
    },
}

# ---------------------------------------------------------------------------
# Scenario A - the committed ladder. Prices and shares are read from
# inputs.json so this file cannot drift from the finance model.
# ---------------------------------------------------------------------------
SCENARIO_A_GATE = {
    "Team": "core memory, full 129-domain read surface, no epistemic partition",
    "Business": "+ epistemic partition (grounded/simulated), provenance ledger, "
                "contamination audit",
    "Scale": "+ A2A transport, multi-region, SSO/SCIM",
    "Enterprise": "+ BYOC, custom domains, contractual SLA",
}

# ---------------------------------------------------------------------------
# Scenario B - proposed 4.0 repackaging. Same four list prices. The change is
# that the governance capability moves OUT of Team and INTO Business, which
# pulls part of the Team book up a tier.
# ---------------------------------------------------------------------------
SCENARIO_B_SHARES = {"Team": 0.58, "Business": 0.24, "Scale": 0.14, "Enterprise": 0.04}
SCENARIO_B_GATE = {
    "Team": "core memory, full 129-domain read surface, 90-day ledger retention, "
            "no epistemic partition",
    "Business": "+ epistemic partition, unlimited ledger retention, contamination "
                "audit, evidence-based promotion",
    "Scale": "+ A2A transport, multi-region, SSO/SCIM, 99.9% SLA",
    "Enterprise": "+ BYOC, custom domains, 99.95% SLA, named TAM",
}


def load():
    if not os.path.exists(INPUTS):
        print("cannot run: %s not found" % INPUTS, file=sys.stderr)
        sys.exit(2)
    with open(INPUTS) as fh:
        return json.load(fh)


def largest_remainder(shares, total):
    """Integer account book from fractional shares, largest-remainder method.

    Ties are broken by tier order (Team, Business, Scale, Enterprise) so the
    result is deterministic and reproducible.
    """
    raw = {t: shares[t] * total for t in shares}
    floors = {t: int(raw[t]) for t in raw}
    short = total - sum(floors.values())
    order = sorted(raw, key=lambda t: (-(raw[t] - floors[t]), list(shares).index(t)))
    for t in order[:short]:
        floors[t] += 1
    return floors


def tier_economics(prices, shares, cogs):
    """Per-tier contribution, gross profit and concentration.

    Two views are reported and they are NOT the same number:

    * ``blended_acv_fractional_usd`` - the share-weighted blend. This is the
      house figure's definition and it is what the invariant is checked on.
    * ``blended_acv_usd`` - the blend of the integer account book produced by
      largest-remainder rounding. An integer book cannot reproduce a fractional
      blend exactly, so this carries a disclosed residual. The repo already
      documents the admissible band ($13,983.33 to $14,233.33) in
      docs/pricing/tier-price-derivation.csv; this model reproduces it rather
      than pretending the rounding is free.
    """
    book = largest_remainder(shares, HOUSE_ACCOUNTS)
    rows = []
    for t in prices:
        price = prices[t]
        gp = price - cogs
        rows.append({
            "tier": t,
            "acv_usd": price,
            "share": shares[t],
            "accounts": book[t],
            "fractional_accounts": round(shares[t] * HOUSE_ACCOUNTS, 4),
            "cogs_usd": cogs,
            "gross_profit_per_account_usd": gp,
            "gross_margin_pct": round(100.0 * gp / price, 2),
            "max_discount_before_zero_contribution_pct": round(100.0 * gp / price, 2),
            "revenue_usd": book[t] * price,
            "gross_profit_usd": book[t] * gp,
        })
    rev = sum(r["revenue_usd"] for r in rows)
    gp = sum(r["gross_profit_usd"] for r in rows)
    logos = sum(r["accounts"] for r in rows)
    for r in rows:
        r["logo_share_pct"] = round(100.0 * r["accounts"] / logos, 2)
        r["gp_share_pct"] = round(100.0 * r["gross_profit_usd"] / gp, 2)
        # leverage = share of gross profit per share of logos. <1 means the tier
        # consumes more logo effort than it returns in margin.
        r["gp_leverage_x"] = round(r["gp_share_pct"] / r["logo_share_pct"], 2)
    fractional = sum(shares[t] * prices[t] for t in prices)
    return {
        "tiers": rows,
        "accounts": logos,
        "revenue_usd": rev,
        "gross_profit_usd": gp,
        "gross_margin_pct": round(100.0 * gp / rev, 2),
        "blended_acv_fractional_usd": round(fractional, 4),
        "blended_acv_usd": round(rev / logos, 2),
        "rounding_residual_usd": round(rev / logos - fractional, 2),
        "rounding_note": "integer account book vs fractional share blend; the "
                         "residual is a rounding artefact, not a price change",
    }


def _vw_meter(pts):
    """Van Westendorp-style meter over one published price distribution."""
    pts = sorted(pts)
    n = len(pts)
    if n == 0:
        return None
    pmc = pts[n // 2] if n % 2 else (pts[n // 2 - 1] + pts[n // 2]) / 2.0
    return {
        "n_points": n,
        "min_usd": pts[0],
        "point_of_marginal_cheapness_usd": pmc,
        "indifference_price_usd": pmc,
        "optimal_price_point_usd": pts[int(n * 0.75)] if n > 1 else pts[0],
        "point_of_marginal_expensiveness_usd": pts[-1],
        "ceiling_usd": pts[-1],
        "median_usd": pmc,
    }


def wtp_analysis():
    """Willingness-to-pay evidence from PUBLISHED price points, by segment.

    This is a proxy, not primary research. It answers "where does each budget
    line actually transact", not "what would a mem20 buyer say in an interview".

    The segments are kept apart on purpose. A vector-store minimum and a
    governance platform tier are not memory-API prices, and folding them into
    one distribution would manufacture a ceiling that no memory buyer ever
    agreed to pay. Only the memory_api segment sets the category ceiling.
    """
    by_seg = {}
    for p in COMPETITOR_POINTS:
        by_seg.setdefault(p[4], []).append(p[2])

    mem = _vw_meter(by_seg.get("memory_api", []))
    sub = _vw_meter(by_seg.get("substrate", []))
    gov = _vw_meter(by_seg.get("governance", []))

    ceiling = mem["ceiling_usd"]
    team = 6000
    business = 18000
    return {
        "method": "Van Westendorp proxy over published competitor price points, "
                  "computed per segment",
        "caveat": "PROXY, not primary research. Published points only; vendors "
                  "that publish no price (Mem0 Custom, Zep Enterprise, Cognee "
                  "Enterprise, ServiceNow) are excluded rather than estimated.",
        "points_used": [{"player": p[0], "plan": p[1], "usd_per_year": p[2],
                         "source_id": p[3], "segment": p[4], "note": p[5]}
                        for p in COMPETITOR_POINTS],
        "memory_api_meter": mem,
        "substrate_meter": sub,
        "governance_meter": gov,
        "category_ceiling_usd": ceiling,
        "category_ceiling_source": "Zep Flex Plus, $375/mo annualised (S5)",
        "mem20_team_usd": team,
        "team_premium_vs_ceiling_pct": round(100.0 * (team - ceiling) / ceiling, 2),
        "team_multiple_of_ceiling_x": round(team / ceiling, 2),
        "pct_of_memory_points_below_team": round(
            100.0 * sum(1 for p in by_seg["memory_api"] if p <= team)
            / len(by_seg["memory_api"]), 2),
        "governance_anchor_low_usd": GOVERNANCE_ANCHOR_LOW,
        "governance_anchor_high_usd": GOVERNANCE_ANCHOR_HIGH,
        "business_tier_vs_governance_anchor_pct": round(
            100.0 * (business - GOVERNANCE_ANCHOR_HIGH) / GOVERNANCE_ANCHOR_HIGH, 2),
        "finding": (
            "Two separate budget lines, and mem20 is mispriced against both. "
            "(1) MEMORY API: the highest published price point is $%s (Zep Flex "
            "Plus); mem20's entry tier is $%s, i.e. %+.0f%% versus that ceiling, "
            "and 100%% of published memory-API points sit at or below it. mem20 "
            "has no land tier - every buyer enters at 1.3x the category's top "
            "published price. (2) GOVERNANCE: the audit/control budget line "
            "transacts at $%s-$%s (Lyzr platform top tier, S29). mem20's Business "
            "tier at $%s is %+.0f%% versus that anchor, so the governance "
            "capability is priced correctly at Business - and is given away "
            "inside Team, which is the leak quantified in margin_leak."
            % (format(ceiling, ","), format(team, ","),
               100.0 * (team - ceiling) / ceiling,
               format(GOVERNANCE_ANCHOR_LOW, ","),
               format(GOVERNANCE_ANCHOR_HIGH, ","), format(business, ","),
               100.0 * (business - GOVERNANCE_ANCHOR_HIGH) / GOVERNANCE_ANCHOR_HIGH)
        ),
    }


def margin_leak(scen_a, cogs):
    """Quantify the cost of bundling the governance moat into the entry tier.

    The leak is the gross profit forgone by selling the governance bundle at
    Team's price instead of at Business's price, for the share of Team buyers
    who would have paid for it separately.
    """
    team = next(r for r in scen_a["tiers"] if r["tier"] == "Team")
    business = next(r for r in scen_a["tiers"] if r["tier"] == "Business")
    attach = ASSUMPTIONS["governance_attach_rate_baseline"]["value"]
    uplift_per_account = business["acv_usd"] - team["acv_usd"]
    eligible = team["accounts"] * attach
    forgone = eligible * uplift_per_account
    return {
        "mechanism": "governance capability (epistemic partition + provenance "
                     "ledger + contamination audit) is included in Team at $6,000 "
                     "instead of sold at Business at $18,000",
        "team_accounts": team["accounts"],
        "attach_rate_assumed": attach,
        "eligible_accounts": round(eligible, 2),
        "uplift_per_account_usd": uplift_per_account,
        "forgone_revenue_usd": round(forgone, 2),
        "forgone_gross_profit_usd": round(forgone, 2),
        "forgone_as_pct_of_scenario_a_gp": round(
            100.0 * forgone / scen_a["gross_profit_usd"], 2),
        "note": "COGS is flat per account in this model, so forgone revenue and "
                "forgone gross profit are the same number. If COGS varied by tier "
                "the gross-profit figure would be the smaller of the two.",
    }


def sensitivity(base_acv, cogs, elasticity, accounts=HOUSE_ACCOUNTS):
    """+/-20% price grid with volume response and break-even elasticity."""
    grid = []
    for step in (-0.20, -0.10, 0.0, 0.10, 0.20):
        price = base_acv * (1 + step)
        # volume response: %dQ = elasticity * %dP
        vol_mult = 1 + elasticity * step
        vol = accounts * vol_mult
        revenue = vol * price
        gp = vol * (price - cogs)
        # win rate moves inversely to price, scaled by the same elasticity
        win = ASSUMPTIONS["win_rate_at_list"]["value"] * vol_mult
        grid.append({
            "price_usd": round(price, 2),
            "delta_pct": round(step * 100, 1),
            "volume_multiple": round(vol_mult, 4),
            "accounts": round(vol, 2),
            "revenue_usd": round(revenue, 2),
            "gross_profit_usd": round(gp, 2),
            "gross_margin_pct": round(100.0 * (price - cogs) / price, 2),
            "win_rate_pct": round(100.0 * win, 2),
        })
    base = next(g for g in grid if g["delta_pct"] == 0.0)
    for g in grid:
        g["revenue_vs_base_pct"] = round(
            100.0 * (g["revenue_usd"] - base["revenue_usd"]) / base["revenue_usd"], 2)
        g["gp_vs_base_pct"] = round(
            100.0 * (g["gross_profit_usd"] - base["gross_profit_usd"])
            / base["gross_profit_usd"], 2)

    # Break-even elasticity: the elasticity at which a 10% cut leaves gross
    # profit unchanged. Solve (1+e*d)*(p*(1+d)-c) = p-c for e.
    d = -0.10
    p = base_acv
    e_be = ((p - cogs) / (p * (1 + d) - cogs) - 1) / d
    return {
        "base_acv_usd": base_acv,
        "cogs_usd": cogs,
        "elasticity_assumed": elasticity,
        "grid": grid,
        "break_even_elasticity_10pct_cut": round(e_be, 3),
        "break_even_note": (
            "A 10%% list cut holds gross profit only while elasticity is shallower "
            "than %.2f. At the assumed %.1f the cut is gross-profit-negative, which "
            "is why discount depth - not list price - is the lever to control."
            % (e_be, elasticity)
        ),
    }


def discount_governance(scen):
    """Discount depth caps tied to the contribution floor of each tier."""
    rows = []
    for r in scen["tiers"]:
        gm = r["gross_margin_pct"]
        # Hard cap: never discount past the point where contribution falls below
        # 20% of list gross profit. That is a policy choice, stated as such.
        policy_cap = max(0.0, gm - 20.0)
        rows.append({
            "tier": r["tier"],
            "gross_margin_pct": gm,
            "absolute_cap_pct": gm,
            "policy_cap_pct": round(policy_cap, 2),
            "approval": ("Sales rep" if policy_cap <= 10 else
                         "Sales manager" if policy_cap <= 20 else
                         "VP Sales" if policy_cap <= 40 else "CEO/CFO"),
            "note": ("binding constraint: any discount above %.2f%% makes this "
                     "tier contribution-negative" % gm),
        })
    return {
        "policy": "cap = gross margin - 20pp; never discount a tier below 20% of "
                  "its list gross profit",
        "tiers": rows,
        "binding_tier": min(rows, key=lambda r: r["policy_cap_pct"])["tier"],
    }


def build(data):
    house = data["house_numbers"]
    ladder = data["tier_ladder"]
    uc = data["unit_cost_and_funnel"]

    cogs = (uc["hosting_cost_per_account_usd"]
            + data["acquisition_inputs"]["tickets_per_account"]
            * data["acquisition_inputs"]["cost_per_ticket_usd"])

    prices_a = {t["tier"]: t["acv_usd"] for t in ladder}
    shares_a = {t["tier"]: t["share"] for t in ladder}

    scen_a = tier_economics(prices_a, shares_a, cogs)
    scen_b = tier_economics(prices_a, SCENARIO_B_SHARES, cogs)

    # Invariant checks - refuse to emit a drifted figure.
    # The house blend is the FRACTIONAL share-weighted blend. The integer book
    # blend is reported alongside it with its residual disclosed, never asserted
    # equal to the house figure.
    problems = []
    if abs(scen_a["blended_acv_fractional_usd"] - HOUSE_ACV) > 0.01:
        problems.append("scenario A fractional blend %.4f != house %d"
                        % (scen_a["blended_acv_fractional_usd"], HOUSE_ACV))
    if abs(scen_b["blended_acv_fractional_usd"] - 16040.0) > 0.01:
        problems.append("scenario B fractional blend %.4f != 16040"
                        % scen_b["blended_acv_fractional_usd"])
    if abs(sum(shares_a.values()) - 1.0) > 1e-9:
        problems.append("scenario A shares sum to %.6f" % sum(shares_a.values()))
    if abs(sum(SCENARIO_B_SHARES.values()) - 1.0) > 1e-9:
        problems.append("scenario B shares sum to %.6f" % sum(SCENARIO_B_SHARES.values()))
    if scen_a["accounts"] != HOUSE_ACCOUNTS:
        problems.append("scenario A book is %d accounts, not %d"
                        % (scen_a["accounts"], HOUSE_ACCOUNTS))
    if scen_b["accounts"] != HOUSE_ACCOUNTS:
        problems.append("scenario B book is %d accounts, not %d"
                        % (scen_b["accounts"], HOUSE_ACCOUNTS))
    if house["som_accounts"] * house["blended_acv_usd"] != house["som_arr_usd"]:
        problems.append("house SOM identity does not hold")

    out = {
        "schema": "mem20.pricing.model/4.0",
        "as_of": "2026-11-16",
        "release": "4.0.0",
        "surface": {"tools": 487, "domains": 129,
                    "source": "docs/surface.json (live pin)"},
        "invariants": {
            "blended_acv_usd": HOUSE_ACV,
            "som_arr_usd": HOUSE_SOM,
            "som_accounts": HOUSE_ACCOUNTS,
            "tam_usd": HOUSE_TAM,
            "sam_usd": HOUSE_SAM,
            "status": "PASS" if not problems else "FAIL",
            "problems": problems,
        },
        "cost_structure": {
            "hosting_per_account_usd": uc["hosting_cost_per_account_usd"],
            "support_per_account_usd": (data["acquisition_inputs"]["tickets_per_account"]
                                        * data["acquisition_inputs"]["cost_per_ticket_usd"]),
            "cogs_per_account_usd": cogs,
            "cogs_basis": "hosting + 24 tickets x $100 x (1 - 0 deflection)",
            "blended_cac_usd": 16800,
            "cac_basis": "32 touches x $210 / 0.40 close, 0 inbound signals",
        },
        "assumptions": ASSUMPTIONS,
        "scenario_a_committed": {
            "label": "committed ladder - 72/12/12/4, blend $14,000, zero drift",
            "gates": SCENARIO_A_GATE,
            **scen_a,
        },
        "scenario_b_proposed": {
            "label": "proposed 4.0 repackaging - 58/24/14/4, blend $16,040",
            "gates": SCENARIO_B_GATE,
            "blend_delta_usd": round(
                scen_b["blended_acv_fractional_usd"] - HOUSE_ACV, 2),
            "blend_delta_pct": round(
                100.0 * (scen_b["blended_acv_fractional_usd"] - HOUSE_ACV)
                / HOUSE_ACV, 2),
            "som_arr_usd": round(
                scen_b["blended_acv_fractional_usd"] * HOUSE_ACCOUNTS, 2),
            "som_delta_usd": round(
                scen_b["blended_acv_fractional_usd"] * HOUSE_ACCOUNTS - HOUSE_SOM, 2),
            "gp_delta_vs_a_usd": round(
                scen_b["gross_profit_usd"] - scen_a["gross_profit_usd"], 2),
            "gp_delta_vs_a_pct": round(
                100.0 * (scen_b["gross_profit_usd"] - scen_a["gross_profit_usd"])
                / scen_a["gross_profit_usd"], 2),
            "requires_owner_signoff": True,
            "why_it_moves_a_house_number": (
                "the mix shift from gating governance out of Team raises the blend "
                "above $14,000, which restates SOM. That is an owner decision; the "
                "model reports the delta and does not write it into inputs.json."
            ),
            **scen_b,
        },
        "wtp": wtp_analysis(),
        "margin_leak": margin_leak(scen_a, cogs),
        "sensitivity": sensitivity(HOUSE_ACV, cogs,
                                   ASSUMPTIONS["price_elasticity"]["value"]),
        "discount_governance": discount_governance(scen_a),
    }
    return out, problems


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------
def write_csv(path, header, rows):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def write_artefacts(m):
    # 1. packaging
    rows = []
    for key, label in (("scenario_a_committed", "A-committed"),
                       ("scenario_b_proposed", "B-proposed")):
        s = m[key]
        for t in s["tiers"]:
            rows.append([
                label, t["tier"], t["acv_usd"], t["share"], t["accounts"],
                t["cogs_usd"], t["gross_profit_per_account_usd"],
                t["gross_margin_pct"], t["logo_share_pct"], t["gp_share_pct"],
                t["gp_leverage_x"], s["gates"][t["tier"]],
            ])
    write_csv(os.path.join(HERE, "pricing_packaging_4.0.csv"),
              ["scenario", "tier", "acv_usd", "share", "accounts", "cogs_usd",
               "gross_profit_per_account_usd", "gross_margin_pct",
               "logo_share_pct", "gp_share_pct", "gp_leverage_x", "capability_gate"],
              rows)

    # 2. WTP evidence
    w = m["wtp"]
    rows = [[p["player"], p["plan"], p["usd_per_year"], p["source_id"],
             p["segment"], p["note"]] for p in w["points_used"]]
    write_csv(os.path.join(HERE, "pricing_wtp_evidence_4.0.csv"),
              ["player", "plan", "usd_per_year", "source_id", "segment", "note"],
              rows)

    # 3. margin structure
    rows = []
    for key, label in (("scenario_a_committed", "A-committed"),
                       ("scenario_b_proposed", "B-proposed")):
        s = m[key]
        for t in s["tiers"]:
            rows.append([label, t["tier"], t["acv_usd"], t["cogs_usd"],
                         t["gross_profit_per_account_usd"], t["gross_margin_pct"],
                         t["revenue_usd"], t["gross_profit_usd"],
                         t["gp_share_pct"], t["gp_leverage_x"]])
        rows.append([label, "TOTAL", s["blended_acv_usd"], "", "",
                     s["gross_margin_pct"], s["revenue_usd"],
                     s["gross_profit_usd"], 100.0, ""])
    write_csv(os.path.join(HERE, "pricing_margin_structure_4.0.csv"),
              ["scenario", "tier", "acv_usd", "cogs_usd",
               "gross_profit_per_account_usd", "gross_margin_pct", "revenue_usd",
               "gross_profit_usd", "gp_share_pct", "gp_leverage_x"], rows)

    # 4. sensitivity
    rows = [[g["delta_pct"], g["price_usd"], g["volume_multiple"], g["accounts"],
             g["revenue_usd"], g["gross_profit_usd"], g["gross_margin_pct"],
             g["win_rate_pct"], g["revenue_vs_base_pct"], g["gp_vs_base_pct"]]
            for g in m["sensitivity"]["grid"]]
    write_csv(os.path.join(HERE, "pricing_sensitivity_4.0.csv"),
              ["delta_pct", "price_usd", "volume_multiple", "accounts",
               "revenue_usd", "gross_profit_usd", "gross_margin_pct",
               "win_rate_pct", "revenue_vs_base_pct", "gp_vs_base_pct"], rows)

    # 5. full model
    with open(os.path.join(HERE, "pricing_model_4.0.json"), "w") as fh:
        json.dump(m, fh, indent=2)
        fh.write("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify invariants only, write nothing")
    args = ap.parse_args()

    m, problems = build(load())
    if problems:
        print("PRICING MODEL INVARIANT DRIFT", file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        return 1

    if not args.check:
        write_artefacts(m)

    a, b = m["scenario_a_committed"], m["scenario_b_proposed"]
    w = m["wtp"]
    print("mem20 4.0 pricing model - OK")
    print("  surface            %d tools / %d domains"
          % (m["surface"]["tools"], m["surface"]["domains"]))
    print("  COGS/account       $%s" % format(m["cost_structure"]["cogs_per_account_usd"], ","))
    print("  A committed        blend $%s (frac) / $%s (book)  GM %.2f%%  GP $%s"
          % (format(a["blended_acv_fractional_usd"], ",.2f"),
             format(a["blended_acv_usd"], ",.2f"), a["gross_margin_pct"],
             format(a["gross_profit_usd"], ",")))
    print("  B proposed         blend $%s (frac) / $%s (book)  GM %.2f%%  GP $%s"
          % (format(b["blended_acv_fractional_usd"], ",.2f"),
             format(b["blended_acv_usd"], ",.2f"), b["gross_margin_pct"],
             format(b["gross_profit_usd"], ",")))
    print("  B vs A             blend %+.2f%%  GP %+.2f%%"
          % (b["blend_delta_pct"], b["gp_delta_vs_a_pct"]))
    print("  category ceiling   $%s  (mem20 Team is %+.0f%% vs it)"
          % (format(w["category_ceiling_usd"], ","),
             w["team_premium_vs_ceiling_pct"]))
    print("  governance anchor  $%s-$%s"
          % (format(w["governance_anchor_low_usd"], ","),
             format(w["governance_anchor_high_usd"], ",")))
    print("  margin leak        $%s forgone GP (%.2f%% of scenario A GP)"
          % (format(m["margin_leak"]["forgone_gross_profit_usd"], ",.2f"),
             m["margin_leak"]["forgone_as_pct_of_scenario_a_gp"]))
    print("  break-even elast.  %.2f (assumed %.1f)"
          % (m["sensitivity"]["break_even_elasticity_10pct_cut"],
             m["sensitivity"]["elasticity_assumed"]))
    print("  (%s)" % ("--check: no artefacts written" if args.check
                      else "artefacts written"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
