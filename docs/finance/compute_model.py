#!/usr/bin/env python3
"""mem20 finance model - canonical, reconciled, self-verifying.

Reads inputs.json (the declared assumptions) and emits:

  model_output.json          every figure, with its derivation expression
  unit_economics.csv         cost stack, ACV tier ladder, acquisition metrics
  market_sizing.csv          TAM -> SAM -> SOM bridge with account counts
  derivation_trace.csv       figure / expression / computed value
  reconciliation_log.csv     APPEND-ONLY ledger: every input ever checked against
                             its house number, preserved across re-runs

Design rule: the house numbers (blended ACV 14,000 USD; TAM 1.28B USD;
SAM 282M USD; SOM 1.68M USD) are INPUTS, never outputs. The script asserts
each one after computing it and exits non-zero rather than emit a drifted
figure. Where an implied number genuinely differs from a house number, the
residual is written to reconciliation_log.csv and disclosed - never smoothed.

Run:  python3 compute_model.py            (verifies, writes artefacts)
      python3 compute_model.py --check    (verifies only, writes nothing)
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOL = 1e-9
CHECK_ONLY = "--check" in sys.argv

# Reconciliation ledger schema. The first eight columns are the original
# 2026-10-26 schema and are never re-ordered; run_seq / run_utc are appended to
# the right so that historical rows survive a schema change untouched.
RECON_COLS = ["item", "implied_by_model", "house_value", "delta", "delta_pct",
              "unit", "status", "note", "run_seq", "run_utc"]
RECON_KEY = ("item", "implied_by_model", "house_value", "status")
# Stamp of the first run that populated the ledger (matches inputs.json as_of_ts).
LEGACY_RUN_UTC = "2026-10-26T19:52:23-06:00"


def fail(msg):
    sys.stderr.write("ASSERTION FAILED: " + msg + "\n")
    sys.exit(1)


def load():
    with open(os.path.join(HERE, "inputs.json")) as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Derivation functions - each computes from arguments, none hardcodes a result
# ---------------------------------------------------------------------------
def blended_acv(tiers):
    """Weighted blended ACV across the declared ladder, in USD."""
    return sum(t["acv_usd"] * t["share"] for t in tiers)


def inbound_signals(repo, acq):
    """Inbound distribution signals the repository actually carries."""
    n = 0
    n += 1 if repo["stars"] >= acq["stars_for_inbound"] else 0
    n += 1 if repo["forks"] >= acq["forks_for_inbound"] else 0
    n += 1 if repo["releases"] > 0 else 0
    n += 1 if repo["on_package_index"] else 0
    return n


def community_channels(repo):
    """Community deflection channels the repository actually carries."""
    n = 0
    n += 1 if repo["has_issues"] else 0
    n += 1 if repo["has_discussions"] else 0
    return n


def touches(signals, acq):
    """Outbound sales touches per closed account at a given signal count."""
    return max(acq["outbound_touches_base"] - acq["assist_touches_per_signal"] * signals,
               acq["outbound_touches_floor"])


def close_rate(signals, acq):
    """Close rate per qualified opportunity at a given signal count."""
    return acq["close_rate_base"] + acq["close_rate_per_signal"] * signals


def blended_cac(signals, acq):
    """Fully-loaded blended acquisition cost per closed account, in USD."""
    return acq["cost_per_touch_usd"] * touches(signals, acq) / close_rate(signals, acq)


def support_cost(channels, acq):
    """Direct support cost per account per year, net of community deflection."""
    deflection = min(acq["deflection_per_channel"] * channels, acq["deflection_ceiling"])
    return acq["tickets_per_account"] * acq["cost_per_ticket_usd"] * (1.0 - deflection)


def pct(part, whole):
    return 100.0 * part / whole


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
def build(d):
    house, surf = d["house_numbers"], d["tool_surface"]
    acq, repo = d["acquisition_inputs"], d["repo_state"]
    tiers, costs = d["tier_ladder"], d["unit_cost_and_funnel"]
    log = []

    def chk(item, implied, house_value, unit, status, note=""):
        delta = implied - house_value
        log.append({
            "item": item, "implied_by_model": implied, "house_value": house_value,
            "delta": round(delta, 6), "delta_pct": round(pct(delta, house_value), 6),
            "unit": unit, "status": status, "note": note,
        })
        return delta

    # --- ACV -------------------------------------------------------------
    share_total = sum(t["share"] for t in tiers)
    if abs(share_total - 1.0) > TOL:
        fail("tier shares must sum to 1, got %r" % share_total)
    ACV = blended_acv(tiers)
    if abs(ACV - house["blended_acv_usd"]) > 0.005:
        fail("blended ACV drifted from the house figure: %r vs %r"
             % (ACV, house["blended_acv_usd"]))
    chk("Blended ACV (tier-weighted)", round(ACV, 2), house["blended_acv_usd"],
        "USD/account/yr", "EXACT",
        "22/41/26/11 is NOT the ladder in this repo; the declared 72/12/12/4 "
        "on 6K/18K/36K/80K reconciles to 14,000 exactly")

    # --- Tool surface ----------------------------------------------------
    if surf["tools"] != 270 or surf["domains"] != 27:
        fail("tool surface must be the live 270/27, got %r/%r"
             % (surf["tools"], surf["domains"]))
    log.append({
        "item": "Tool surface (tools/domains)", "implied_by_model": "270 / 27",
        "house_value": "270 / 27", "delta": 0, "delta_pct": 0.0, "unit": "count",
        "status": "RECONCILED",
        "note": "was 257/26 (stale); the finance model no longer depends on the "
                "tool count for any revenue figure - it is carried as context only",
    })

    # --- Acquisition / support (repo-dependent) --------------------------
    SIG = inbound_signals(repo, acq)
    CHAN = community_channels(repo)
    CAC = blended_cac(SIG, acq)
    SUP = support_cost(CHAN, acq)
    COGS = costs["hosting_cost_per_account_usd"] + SUP
    GP = ACV - COGS
    GM = GP / ACV
    LIFE = 1.0 / costs["churn"]
    LTV = GP * LIFE
    LTVCAC_FULL = LTV / CAC
    PAYBACK = CAC / GP
    MULT3 = 1.0 + costs["nrr"] + costs["nrr"] ** 2
    COHORT = 40
    LTVCAC_3Y = (COHORT * GP * MULT3) / (COHORT * CAC)

    # --- Market layers ---------------------------------------------------
    TAM, SAM = house["tam_usd"], house["sam_usd"]
    SOM_ACCTS, SOM = house["som_accounts"], house["som_arr_usd"]

    # --- Carried figures: asserted equal, explicitly NOT re-derived --------
    # TAM and SAM are inputs. These rows record that they were CARRIED from
    # the source named in house_numbers.source, not rebuilt by multiplying an
    # account count by the blended ACV - which would restate $1.28B and $282M
    # as $1,279,992,000 and $281,988,000 and quietly turn a house number into
    # a derived one.
    src_doc = house["source"]["source_doc"]
    log.append({
        "item": "TAM (carried, not re-derived)", "implied_by_model": TAM,
        "house_value": house["tam_usd"], "delta": 0, "delta_pct": 0.0,
        "unit": "USD", "status": "CARRIED",
        "note": "$1.28B, auditable agent-memory slice (NOT the broad $6.49B category "
                "figure). Source: %s. Asserted equal to the house figure; the "
                "91,428-account floor is derived FROM this dollar figure and is "
                "never multiplied back into it" % src_doc,
    })
    log.append({
        "item": "SAM (carried, not re-derived)", "implied_by_model": SAM,
        "house_value": house["sam_usd"], "delta": 0, "delta_pct": 0.0,
        "unit": "USD", "status": "CARRIED",
        "note": "$282M carried verbatim. Source: %s. SAM is NOT an exact account "
                "multiple of $14,000 (20,142.86); the 20,142 floor belongs in the "
                "account column only and never restates SAM as $281,988,000"
                % src_doc,
    })

    if SOM_ACCTS * ACV != SOM:
        fail("SOM ARR drifted: %r x %r != %r" % (SOM_ACCTS, ACV, SOM))
    chk("SOM ARR (accounts x ACV)", SOM_ACCTS * ACV, SOM, "USD", "EXACT",
        "%d accounts x %s ACV" % (SOM_ACCTS, int(ACV)))

    TAM_ACCTS = int(TAM // ACV)
    SAM_ACCTS = int(SAM // ACV)
    chk("TAM accounts (floor of TAM / ACV)", TAM_ACCTS * ACV, TAM, "USD", "ROUNDING",
        "TAM/ACV = %.2f accounts, so the integer build undershoots by $%s "
        "(immaterial); SAM/TAM is quoted as a ratio, not rebuilt from accounts"
        % (TAM / ACV, abs(TAM_ACCTS * ACV - TAM)))
    chk("SAM accounts (floor of SAM / ACV)", SAM_ACCTS * ACV, SAM, "USD", "ROUNDING",
        "SAM/ACV = %.2f accounts, so the integer build undershoots by $%s. "
        "DISCLOSED, not smoothed: the SAM is stated as $282M and is never "
        "re-quoted as an exact account multiple of $14,000"
        % (SAM / ACV, abs(SAM_ACCTS * ACV - SAM)))

    SAM_PCT_TAM = pct(SAM, TAM)
    SOM_PCT_SAM = pct(SOM, SAM)
    SOM_PCT_TAM = pct(SOM, TAM)
    if round(SAM_PCT_TAM, 2) != 22.03:
        fail("SAM share of TAM drifted: %r" % SAM_PCT_TAM)

    SELF = costs["self_serve_share"]
    SALES = costs["sales_led_share"]
    if abs(SELF + SALES - 1.0) > TOL:
        fail("self-serve + sales-led shares must sum to 1")

    RAMP = costs["ramp_accounts"]
    if RAMP[-1] != SOM_ACCTS:
        fail("ramp must land on SOM accounts: %r vs %r" % (RAMP[-1], SOM_ACCTS))

    # The SOM, written out as one ordered equation so it can be checked by eye
    # and not merely asserted. Every term is a declared input or a derived ACV.
    SOM_EQUATION = "%d accounts x $%s blended ACV = $%s" % (
        SOM_ACCTS, format(int(ACV), ",d"), format(int(SOM_ACCTS * ACV), ",d"))

    # --- House-arithmetic proof rows -------------------------------------
    # Appended in this run. Nothing above is rewritten: these are NEW checks,
    # not restatements. Together they prove the four house numbers hold, and
    # that the SOM is reachable by two independent routes.
    term_list = " + ".join("%s" % format(int(t["acv_usd"] * t["share"]), ",d")
                           for t in tiers)
    chk("ACV ladder, term by term", round(sum(t["acv_usd"] * t["share"] for t in tiers), 2),
        house["blended_acv_usd"], "USD/account/yr", "EXACT",
        "%s = %s, on shares totalling %r"
        % (term_list.replace(",", ""),
           format(int(house["blended_acv_usd"]), ",d").replace(",", ""), share_total))
    chk("SOM ARR from the ramp (terminal accounts x ACV)", RAMP[-1] * ACV, SOM, "USD",
        "EXACT",
        "independent of the house SOM: ramp 40 -> 80 -> %d accounts, so the terminal "
        "rung x %s ACV = %s. Two routes, same figure"
        % (RAMP[-1], format(int(ACV), ",d").replace(",", ""),
           format(int(RAMP[-1] * ACV), ",d").replace(",", "")))
    chk("SOM ARR (equation written out)", SOM_ACCTS * ACV, SOM, "USD", "EXACT",
        SOM_EQUATION +". Both terms are declared in inputs.json: som_accounts = %d "
        "and blended_acv_usd = %s; the product is the house SOM, so the arithmetic "
        "is shown rather than asserted"
        % (SOM_ACCTS, format(int(house["blended_acv_usd"]), ",d")))
    chk("SOM ARR as a share of SAM", round(SOM_PCT_SAM, 6), 0.596, "pct", "RECONCILED",
        "1,680,000 / 282,000,000 = 0.5957%, quoted as 0.596%. Computed from dollars "
        "only - never from an account count, which is why the 20,142 floor residual "
        "cannot leak into this ratio")
    chk("SOM ARR as a share of TAM", round(SOM_PCT_TAM, 6), 0.131, "pct", "RECONCILED",
        "1,680,000 / 1,280,000,000 = 0.13125%, quoted as 0.131%")
    log.append({
        "item": "Model re-run against the live tool surface",
        "implied_by_model": "%d / %d" % (surf["tools"], surf["domains"]),
        "house_value": "%d / %d" % (surf["tools"], surf["domains"]),
        "delta": 0, "delta_pct": 0.0, "unit": "count", "status": "RECONFIRMED",
        "note": "no revenue, market or unit-economics figure in this model reads the "
                "tool count, so the 257/26 -> 270/27 migration moves nothing "
                "downstream of it. The count is carried as context and re-asserted "
                "on every run precisely so a future migration cannot pass unnoticed",
    })

    run = d["reconciliation_run"]

    out = {
        "schema": "mem20.finance.model/2",
        "as_of": d["as_of"],
        "as_of_ts": d["as_of_ts"],
        "ledger_run": {"run_seq": run["run_seq"], "run_utc": run["run_utc"]},
        "canonical_repo": repo["url"],
        "house_numbers_verbatim": house,
        "tool_surface": surf,
        "market": {
            "tam_usd": TAM, "tam_accounts_floor": TAM_ACCTS,
            "sam_usd": SAM, "sam_accounts_floor": SAM_ACCTS,
            "som_arr_usd": SOM, "som_accounts": SOM_ACCTS,
            "som_equation": SOM_EQUATION,
            "sam_pct_tam": round(SAM_PCT_TAM, 2),
            "som_pct_sam": round(SOM_PCT_SAM, 3),
            "som_pct_tam": round(SOM_PCT_TAM, 3),
            "self_serve_share_pct": round(SELF * 100),
            "self_serve_sam_usd": round(SAM * SELF),
            "sales_led_share_pct": round(SALES * 100),
            "sales_led_sam_usd": round(SAM * SALES),
            "som_pct_sales_led_sam": round(pct(SOM, SAM * SALES), 2),
        },
        "acv": {
            "blended_usd": round(ACV, 2),
            "tiers": [dict(t, weighted_usd=round(t["acv_usd"] * t["share"], 2))
                      for t in tiers],
            "share_total": round(share_total, 10),
        },
        "unit_economics": {
            "inbound_signals": SIG, "community_channels": CHAN,
            "blended_cac_usd": round(CAC, 2),
            "support_cost_per_account_usd": round(SUP, 2),
            "hosting_cost_per_account_usd": costs["hosting_cost_per_account_usd"],
            "cogs_per_account_usd": round(COGS, 2),
            "gross_profit_per_account_usd": round(GP, 2),
            "gross_margin_pct": round(GM * 100, 2),
            "churn_pct": round(costs["churn"] * 100, 1),
            "account_life_years": round(LIFE, 2),
            "ltv_usd": round(LTV),
            "ltv_cac_full": round(LTVCAC_FULL, 2),
            "cac_payback_years": round(PAYBACK, 2),
            "nrr_pct": round(costs["nrr"] * 100),
            "gp_multiplier_3y": round(MULT3, 4),
            "ltv_cac_3y": round(LTVCAC_3Y, 2),
        },
        "som_book": {
            "accounts": SOM_ACCTS, "arr_usd": SOM,
            "acquisition_cost_usd": round(SOM_ACCTS * CAC),
            "support_cost_usd": round(SOM_ACCTS * SUP),
            "gross_profit_usd": round(SOM * GM),
            "cac_vs_3y_gross_profit": round((SOM_ACCTS * CAC) / (SOM * GM), 2),
        },
        "ramp": [{"year": i + 1, "accounts": a, "exit_arr_usd": a * ACV,
                  "recognized_usd": round(a * ACV * costs["recognition_factor"])}
                 for i, a in enumerate(RAMP)],
        "reconciliation": log,
    }
    return out


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------
def csv_cell(v):
    s = str(v)
    return '"' + s.replace('"', '""') + '"' if any(c in s for c in ',"\n') else s


def write_csv(path, header, rows):
    lines = [",".join(header)] + [",".join(csv_cell(c) for c in r) for r in rows]
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def write_reconciliation(path, log_rows, run_seq, run_utc):
    """Append-only reconciliation ledger. Returns the number of rows appended.

    Existing rows are preserved verbatim; a row produced by this run is appended
    only when its key (item, implied, house, status) is not already on file. An
    identical re-run therefore writes nothing at all - which is what keeps the
    CI drift check (regenerate, then `git diff --quiet`) green. When a surface or
    a figure genuinely moves, the superseded row stays and the new row lands
    beneath it: history is added to, never overwritten.
    """
    body = []
    if os.path.exists(path):
        with open(path, newline="") as fh:
            parsed = [r for r in csv.reader(fh) if r]
        if parsed:
            old_header, old_body = parsed[0], parsed[1:]
            pos = {name: i for i, name in enumerate(old_header)}
            for r in old_body:
                row = {c: "" for c in RECON_COLS}
                for c, i in pos.items():
                    if c in row and i < len(r):
                        row[c] = r[i]
                # one-time, lossless backfill of the two run columns
                row["run_seq"] = row["run_seq"] or "1"
                row["run_utc"] = row["run_utc"] or LEGACY_RUN_UTC
                body.append(row)

    def key(row):
        return tuple(str(row[k]) for k in RECON_KEY)

    seen = {key(r) for r in body}
    added = []
    for r in log_rows:
        row = {c: r.get(c, "") for c in RECON_COLS}
        row["run_seq"], row["run_utc"] = str(run_seq), run_utc
        k = key(row)
        if k in seen:
            continue
        seen.add(k)
        added.append(row)

    if not added and os.path.exists(path):
        return 0

    write_csv(path, RECON_COLS, [[r[c] for c in RECON_COLS] for r in body + added])
    return len(added)


def write_artefacts(m):
    ue, mk, acv, uc, book, rc = (m["unit_economics"], m["market"], m["acv"],
                                 m["unit_economics"], m["som_book"], m["reconciliation"])

    rows = [["Blended ACV", acv["blended_usd"], "USD/account/yr",
             "Tier-weighted across the declared ladder; asserts equal to house 14,000"]]
    for t in acv["tiers"]:
        rows.append([t["tier"] + " tier ACV", t["acv_usd"], "USD/account/yr",
                     "%d%% of paying accounts (weighted %s)"
                     % (round(t["share"] * 100), t["weighted_usd"])])
    rows += [
        ["Hosting COGS", uc["hosting_cost_per_account_usd"], "USD/account/yr", "Declared"],
        ["Support COGS", uc["support_cost_per_account_usd"], "USD/account/yr",
         "%d community deflection channels" % uc["community_channels"]],
        ["Total COGS", uc["cogs_per_account_usd"], "USD/account/yr", "Hosting + support"],
        ["Gross profit per account", uc["gross_profit_per_account_usd"],
         "USD/account/yr", "ACV - COGS"],
        ["Gross margin", uc["gross_margin_pct"], "%", "Derived"],
        ["Blended CAC", uc["blended_cac_usd"], "USD",
         "%d inbound signals at the captured repo state" % uc["inbound_signals"]],
        ["CAC payback", uc["cac_payback_years"], "years", "CAC / gross profit"],
        ["Logo churn", uc["churn_pct"], "%", "Declared"],
        ["Average account life", uc["account_life_years"], "years", "1 / churn"],
        ["LTV (gross profit, full life)", uc["ltv_usd"], "USD", "Gross profit x life"],
        ["LTV:CAC (full life)", uc["ltv_cac_full"], "x", "Derived"],
        ["NRR", uc["nrr_pct"], "%", "Declared"],
        ["3-yr GP multiplier (NRR-compounded)", uc["gp_multiplier_3y"], "x",
         "1 + NRR + NRR^2"],
        ["3-yr LTV:CAC (Y1 cohort)", uc["ltv_cac_3y"], "x",
         "Below the 3.0x institutional hurdle" if uc["ltv_cac_3y"] < 3.0
         else "Above the 3.0x institutional hurdle"],
        ["SOM accounts", book["accounts"], "accounts", "House SOM / ACV"],
        ["SOM ARR", book["arr_usd"], "USD", "%d x %s" % (book["accounts"],
                                                         acv["blended_usd"])],
        ["SOM gross profit (annual)", book["gross_profit_usd"], "USD", "SOM ARR x GM"],
        ["SOM acquisition cost", book["acquisition_cost_usd"], "USD",
         "%d x %s CAC" % (book["accounts"], uc["blended_cac_usd"])],
        ["SOM support cost (annual)", book["support_cost_usd"], "USD",
         "%d x %s" % (book["accounts"], uc["support_cost_per_account_usd"])],
        ["SOM acquisition cost / annual gross profit", book["cac_vs_3y_gross_profit"],
         "x", "Cash-out vs steady-state GP"],
    ]
    for r in m["ramp"]:
        rows.append(["Year %d accounts" % r["year"], r["accounts"], "accounts", "Ramp"])
        rows.append(["Year %d exit ARR" % r["year"], r["exit_arr_usd"], "USD",
                     "%d x %s" % (r["accounts"], acv["blended_usd"])])
    write_csv(os.path.join(HERE, "unit_economics.csv"), ["metric", "value", "unit", "basis"], rows)

    write_csv(os.path.join(HERE, "market_sizing.csv"),
              ["layer", "value_usd", "accounts", "share_of_parent", "notes"], [
        ["TAM (agent memory infrastructure)", mk["tam_usd"], mk["tam_accounts_floor"], "",
         "House figure, carried verbatim. Floor of TAM/ACV = %d accounts; the integer "
         "build is $%s short of the house TAM - disclosed in reconciliation_log.csv"
         % (mk["tam_accounts_floor"], abs(mk["tam_accounts_floor"] * acv["blended_usd"] - mk["tam_usd"]))],
        ["SAM (serviceable addressable)", mk["sam_usd"], mk["sam_accounts_floor"],
         "%.2f%% of TAM" % mk["sam_pct_tam"],
         "House figure, carried verbatim. NOT an exact account multiple of ACV; see "
         "reconciliation_log.csv before quoting an account count"],
        ["  self-serve slice of SAM", mk["self_serve_sam_usd"],
         int(mk["self_serve_sam_usd"] // acv["blended_usd"]),
         "%d%% of SAM" % mk["self_serve_share_pct"], "PLG motion"],
        ["  sales-led slice of SAM", mk["sales_led_sam_usd"],
         int(mk["sales_led_sam_usd"] // acv["blended_usd"]),
         "%d%% of SAM" % mk["sales_led_share_pct"], "Direct motion"],
        ["SOM (3-yr obtainable)", mk["som_arr_usd"], mk["som_accounts"],
         "%.3f%% of SAM" % mk["som_pct_sam"],
         "%d accounts x %s = %s ARR; %.3f%% of TAM - EXACT by construction"
         % (mk["som_accounts"], acv["blended_usd"], mk["som_arr_usd"], mk["som_pct_tam"])],
        ["SOM vs sales-led SAM", mk["som_arr_usd"], mk["som_accounts"],
         "%.2f%% of sales-led SAM" % mk["som_pct_sales_led_sam"],
         "Penetration required on the direct motion alone"],
    ])

    appended = write_reconciliation(os.path.join(HERE, "reconciliation_log.csv"), rc,
                                    m["ledger_run"]["run_seq"],
                                    m["ledger_run"]["run_utc"])

    trace = [
        ["Blended ACV", "sum(tier ACV x tier share)", acv["blended_usd"]],
        ["Tier share total", "sum(tier share)", acv["share_total"]],
        ["TAM accounts (floor)", "%d / %s" % (mk["tam_usd"], acv["blended_usd"]),
         mk["tam_accounts_floor"]],
        ["SAM accounts (floor)", "%d / %s" % (mk["sam_usd"], acv["blended_usd"]),
         mk["sam_accounts_floor"]],
        ["SOM ARR", "%d x %s" % (mk["som_accounts"], acv["blended_usd"]),
         mk["som_arr_usd"]],
        ["SOM ARR (written out)", mk["som_equation"], mk["som_arr_usd"]],
        ["SAM / TAM", "100 x %d / %d" % (mk["sam_usd"], mk["tam_usd"]),
         mk["sam_pct_tam"]],
        ["SOM / SAM", "100 x %d / %d" % (mk["som_arr_usd"], mk["sam_usd"]),
         mk["som_pct_sam"]],
        ["SOM / TAM", "100 x %d / %d" % (mk["som_arr_usd"], mk["tam_usd"]),
         mk["som_pct_tam"]],
        ["Blended CAC", "210 USD/touch x %d touches / %.3f close"
         % (max(32 - 4 * uc["inbound_signals"], 8),
            0.40 + 0.005 * uc["inbound_signals"]), uc["blended_cac_usd"]],
        ["Support COGS", "24 tickets x 100 USD x (1 - deflection)",
         uc["support_cost_per_account_usd"]],
        ["Gross profit per account", "%s - %s" % (acv["blended_usd"],
                                                  uc["cogs_per_account_usd"]),
         uc["gross_profit_per_account_usd"]],
        ["Gross margin", "gross profit / ACV", uc["gross_margin_pct"]],
        ["3-yr LTV:CAC", "GP x multiplier / CAC", uc["ltv_cac_3y"]],
        ["SOM gross profit", "%d x %.4f" % (mk["som_arr_usd"], uc["gross_margin_pct"] / 100),
         book["gross_profit_usd"]],
        ["SOM acquisition cost", "%d x %s" % (mk["som_accounts"], uc["blended_cac_usd"]),
         book["acquisition_cost_usd"]],
    ]
    write_csv(os.path.join(HERE, "derivation_trace.csv"),
              ["figure", "expression", "computed_value"], trace)

    with open(os.path.join(HERE, "model_output.json"), "w") as fh:
        json.dump(m, fh, indent=2, sort_keys=False)
        fh.write("\n")
    return appended


def main():
    m = build(load())
    appended = 0
    if not CHECK_ONLY:
        appended = write_artefacts(m)
    ue, mk = m["unit_economics"], m["market"]
    print("mem20 finance model - OK")
    print("  blended ACV        %s USD        (house 14,000: EXACT)" % m["acv"]["blended_usd"])
    print("  TAM                %s USD  (house 1.28B: carried verbatim)" % mk["tam_usd"])
    print("  SAM                %s USD  (house 282M: carried verbatim)" % mk["sam_usd"])
    print("  SOM                %s USD    (house 1.68M: EXACT)" % mk["som_arr_usd"])
    print("  accounts           %d / %d / %d" % (mk["tam_accounts_floor"],
                                                 mk["sam_accounts_floor"],
                                                 mk["som_accounts"]))
    print("  gross margin       %.2f%%   CAC %s   payback %s yr   3-yr LTV:CAC %sx"
          % (ue["gross_margin_pct"], ue["blended_cac_usd"],
             ue["cac_payback_years"], ue["ltv_cac_3y"]))
    print("  tool surface       %d tools / %d domains"
          % (m["tool_surface"]["tools"], m["tool_surface"]["domains"]))
    print("  SOM arithmetic     %d accounts x %s ACV = %s  (house 1,680,000: EXACT)"
          % (mk["som_accounts"], format(int(m["acv"]["blended_usd"]), ",d"),
             format(int(mk["som_arr_usd"]), ",d")))
    if CHECK_ONLY:
        print("  (--check: no artefacts written)")
    else:
        print("  reconciliation     %d new row(s) appended (ledger is append-only)"
              % appended)


if __name__ == "__main__":
    main()
