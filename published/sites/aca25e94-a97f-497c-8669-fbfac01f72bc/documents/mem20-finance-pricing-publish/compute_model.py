#!/usr/bin/env python3
"""mem20 finance model - canonical-repo rebase.

Deterministic and offline. Declared inputs are the model assumptions; the
repo-dependent lines - blended acquisition cost, direct support cost, gross
margin and the three-year LTV:CAC ratio - are computed at run time from the
declared canonical repository state below. The house figures (blended ACV
14,000 USD; TAM 1.28B USD; SAM 282M USD; SOM 1.68M USD) are preserved exactly.
The model asserts its own invariants and exits non-zero rather than emit a
drifted figure.

Run:  python3 compute_model.py
"""
import json

AS_OF = "2026-10-14"
AS_OF_TS = "2026-10-14T16:39:02Z"          # canonical HEAD commit timestamp
TOLERANCE = 1e-9

# ---------------------------------------------------------------------------
# Declared canonical repository state (GitHub REST API, captured 2026-10-14)
# ---------------------------------------------------------------------------
CANONICAL_REPO = {
    "full_name": "bythewayz66-glitch/mem20",
    "url": "https://github.com/bythewayz66-glitch/mem20",
    "clone_url": "https://github.com/bythewayz66-glitch/mem20.git",
    "default_branch": "main",
    "head_full": "c274404a116f203b0ed99ab7156e3752f0953ea8",
    "head_short": "c274404",
    "head_date": AS_OF_TS,
    "parent_short": "64c7335",
    "parent_date": "2026-10-06T05:42:07Z",
    "license": "MIT",
    "visibility": "public",
    "created_at": "2026-10-06T05:41:54Z",
    "repo_age_days": 8,
    "git_size_kb": 34552,
    "worktree_mb": 222,
    "tracked_files": 9873,
    "subsystems": 293,
    "tools": 257,
    "domains": 26,
    "stars": 0,
    "forks": 0,
    "watchers": 0,
    "open_issues": 0,
    "releases": 0,
    "contributors": 4,
    "has_issues": False,
    "has_discussions": False,
    "has_wiki": True,
    "on_package_index": False,
    "primary_language": "Python",
    "lang_bytes": {
        "Python": 16490922, "TypeScript": 4057492, "Rust": 527317, "C#": 525082,
        "JavaScript": 323427, "HTML": 136137, "CSS": 85339, "Shell": 27738,
        "Faust": 6999, "Dockerfile": 2287, "Makefile": 1314,
    },
}

# ---------------------------------------------------------------------------
# Superseded repository. Recorded as retired: the URL does not resolve and it
# carries no version and no install path.
# ---------------------------------------------------------------------------
RETIRED_BASIS = {
    "retired_url": "https://github.com/JaysonAIOnline/mem20",
    "retired_status": "HTTP 404 - not public",
    "retired_source": "github.com/JaysonAIOnline/mcp-cognitive-substrate",
    "retired_version_string": "v2.1.0rc2",
    "retired_install": "pip install mem20",
    "retired_install_status": "not on PyPI - the install fails",
    "assumed_inbound_signals": 4,
    "assumed_community_channels": 2,
}

CANONICAL_INSTALL = 'pip install "git+https://github.com/bythewayz66-glitch/mem20.git"'

# ---------------------------------------------------------------------------
# Declared acquisition inputs. Inbound distribution signals that the
# repository actually carries reduce the outbound touch load and lift the close
# rate; with no inbound signal the full outbound load applies.
# ---------------------------------------------------------------------------
OUTBOUND_TOUCHES_BASE = 32
ASSIST_TOUCHES_PER_SIGNAL = 4
OUTBOUND_TOUCHES_FLOOR = 8
CLOSE_RATE_BASE = 0.40
CLOSE_RATE_PER_SIGNAL = 0.005
COST_PER_TOUCH = 210
STARS_FOR_INBOUND = 100
FORKS_FOR_INBOUND = 20

# Declared support inputs. Community deflection channels (an issue tracker, a
# discussion board) each remove part of the direct support load.
TICKETS_PER_ACCOUNT = 24
COST_PER_TICKET = 100
DEFLECTION_PER_CHANNEL = 0.25
DEFLECTION_CEILING = 0.5

# Declared unit costs, ramp and house figures.
HOSTING_COST_PER_ACCOUNT = 1880
HOUSE_ACV = 14000
HOUSE_TAM_USD = 1_280_000_000
HOUSE_SAM_USD = 282_000_000
HOUSE_SOM_ARR = 1_680_000
HOUSE_SOM_ACCOUNTS = 120
CHURN = 0.12
NRR = 1.15
COHORT_ACCOUNTS = 40
SELF_SERVE_SHARE = 0.45
SALES_LED_SHARE = 0.55
ENTERPRISE_CONCESSION_PCT = 0.08
RECOGNITION_FACTOR = 0.55
TIERS = (("Team", 6000, 0.72), ("Business", 18000, 0.12),
         ("Scale", 36000, 0.12), ("Enterprise", 80000, 0.04))
RAMP = ((1, 40), (2, 80), (3, 120))


# ---------------------------------------------------------------------------
# Derivation functions. Each one computes its figure from its arguments.
# ---------------------------------------------------------------------------
def inbound_signal_count(repo):
    """Count the inbound distribution signals the repository actually carries."""
    signals = 0
    if repo["stars"] >= STARS_FOR_INBOUND:
        signals += 1
    if repo["forks"] >= FORKS_FOR_INBOUND:
        signals += 1
    if repo["releases"] > 0:
        signals += 1
    if repo["on_package_index"]:
        signals += 1
    return signals


def community_channel_count(repo):
    """Count the community deflection channels the repository actually carries."""
    channels = 0
    if repo["has_issues"]:
        channels += 1
    if repo["has_discussions"]:
        channels += 1
    return channels


def outbound_touches(signals):
    """Outbound sales touches per closed account at a given inbound signal count."""
    remaining = OUTBOUND_TOUCHES_BASE - ASSIST_TOUCHES_PER_SIGNAL * signals
    if remaining < OUTBOUND_TOUCHES_FLOOR:
        remaining = OUTBOUND_TOUCHES_FLOOR
    return remaining


def close_rate_at(signals):
    """Close rate per qualified opportunity at a given inbound signal count."""
    return CLOSE_RATE_BASE + CLOSE_RATE_PER_SIGNAL * signals


def blended_cac(signals):
    """Fully-loaded blended acquisition cost per closed account, in USD."""
    return COST_PER_TOUCH * outbound_touches(signals) / close_rate_at(signals)


def support_cost_per_account(channels):
    """Direct support cost per account per year, net of community deflection."""
    deflection = DEFLECTION_PER_CHANNEL * channels
    if deflection > DEFLECTION_CEILING:
        deflection = DEFLECTION_CEILING
    return TICKETS_PER_ACCOUNT * COST_PER_TICKET * (1.0 - deflection)


def blended_acv(tiers):
    """Weighted blended ACV across the declared tier ladder, in USD."""
    return sum(price * share for _name, price, share in tiers)


def source_share(lang_bytes, language):
    """Share of the repository source volume written in one language, in percent."""
    total_bytes = sum(lang_bytes.values())
    assert total_bytes > 0, "language byte counts must be non-empty"
    return 100.0 * lang_bytes[language] / total_bytes


# ---------------------------------------------------------------------------
# Derived figures
# ---------------------------------------------------------------------------
tier_share_total = sum(share for _n, _p, share in TIERS)
assert abs(tier_share_total - 1.0) < TOLERANCE, \
    f"tier shares must sum to 1, got {tier_share_total}"
ACV = blended_acv(TIERS)
assert ACV == HOUSE_ACV, f"blended ACV drifted from the house figure: {ACV}"

CANONICAL_SIGNALS = inbound_signal_count(CANONICAL_REPO)
CANONICAL_CHANNELS = community_channel_count(CANONICAL_REPO)
BENCH_SIGNALS = RETIRED_BASIS["assumed_inbound_signals"]
BENCH_CHANNELS = RETIRED_BASIS["assumed_community_channels"]

CAC_CANONICAL = blended_cac(CANONICAL_SIGNALS)
CAC_BENCHMARK = blended_cac(BENCH_SIGNALS)
SUPPORT_CANONICAL = support_cost_per_account(CANONICAL_CHANNELS)
SUPPORT_BENCHMARK = support_cost_per_account(BENCH_CHANNELS)

assert round(CAC_CANONICAL, 2) == 16800.00, \
    f"canonical acquisition cost drifted: {CAC_CANONICAL}"
assert round(SUPPORT_CANONICAL, 2) == 2400.00, \
    f"canonical support cost drifted: {SUPPORT_CANONICAL}"
assert round(CAC_BENCHMARK, 2) == 8000.00, \
    f"retired-basis acquisition cost drifted: {CAC_BENCHMARK}"
assert round(SUPPORT_BENCHMARK, 2) == 1200.00, \
    f"retired-basis support cost drifted: {SUPPORT_BENCHMARK}"

COGS_CANONICAL = HOSTING_COST_PER_ACCOUNT + SUPPORT_CANONICAL
COGS_BENCHMARK = HOSTING_COST_PER_ACCOUNT + SUPPORT_BENCHMARK
GROSS_PROFIT_CANONICAL = ACV - COGS_CANONICAL
GROSS_PROFIT_BENCHMARK = ACV - COGS_BENCHMARK
GM_CANONICAL = GROSS_PROFIT_CANONICAL / ACV
GM_BENCHMARK = GROSS_PROFIT_BENCHMARK / ACV
assert round(GM_CANONICAL * 100, 1) == 69.4, \
    f"canonical gross margin drifted: {GM_CANONICAL * 100}"
assert round(GM_BENCHMARK * 100, 1) == 78.0, \
    f"retired-basis gross margin drifted: {GM_BENCHMARK * 100}"

LIFE_YEARS = 1.0 / CHURN
LTV_FULL = GROSS_PROFIT_CANONICAL * LIFE_YEARS
LTV_CAC_FULL = LTV_FULL / CAC_CANONICAL
PAYBACK_CANONICAL = CAC_CANONICAL / GROSS_PROFIT_CANONICAL
PAYBACK_BENCHMARK = CAC_BENCHMARK / GROSS_PROFIT_BENCHMARK
GP_MULTIPLIER_3Y = 1.0 + NRR + NRR ** 2
COHORT_GP3_CANONICAL = COHORT_ACCOUNTS * GROSS_PROFIT_CANONICAL * GP_MULTIPLIER_3Y
COHORT_GP3_BENCHMARK = COHORT_ACCOUNTS * GROSS_PROFIT_BENCHMARK * GP_MULTIPLIER_3Y
LTVCAC_3Y_CANONICAL = COHORT_GP3_CANONICAL / (COHORT_ACCOUNTS * CAC_CANONICAL)
LTVCAC_3Y_BENCHMARK = COHORT_GP3_BENCHMARK / (COHORT_ACCOUNTS * CAC_BENCHMARK)
assert round(LTVCAC_3Y_CANONICAL, 2) == 2.01, \
    f"canonical three-year LTV:CAC drifted: {LTVCAC_3Y_CANONICAL}"
assert round(LTVCAC_3Y_BENCHMARK, 2) == 4.74, \
    f"retired-basis three-year LTV:CAC drifted: {LTVCAC_3Y_BENCHMARK}"

SOM_ACCOUNTS = HOUSE_SOM_ACCOUNTS
SOM_ARR = SOM_ACCOUNTS * ACV
assert SOM_ARR == HOUSE_SOM_ARR, f"SOM ARR drifted from the house figure: {SOM_ARR}"
TAM_USD = HOUSE_TAM_USD
SAM_USD = HOUSE_SAM_USD
TAM_ACCOUNTS = int(TAM_USD // ACV)
SAM_ACCOUNTS = int(SAM_USD // ACV)
SELF_SERVE_USD = SAM_USD * SELF_SERVE_SHARE
SALES_LED_USD = SAM_USD * SALES_LED_SHARE
SELF_SERVE_ACCOUNTS = int(SELF_SERVE_USD // ACV)
SALES_LED_ACCOUNTS = int(SALES_LED_USD // ACV)
SAM_PCT_TAM = 100.0 * SAM_USD / TAM_USD
SOM_PCT_SAM = 100.0 * SOM_ARR / SAM_USD
SOM_PCT_TAM = 100.0 * SOM_ARR / TAM_USD
SOM_PCT_SALES_LED = 100.0 * SOM_ACCOUNTS / (SALES_LED_USD / ACV)
assert round(SAM_PCT_TAM, 2) == 22.03, f"SAM share of TAM drifted: {SAM_PCT_TAM}"
assert round(SOM_PCT_SAM, 1) == 0.6, f"SOM share of SAM drifted: {SOM_PCT_SAM}"
assert round(SOM_PCT_TAM, 2) == 0.13, f"SOM share of TAM drifted: {SOM_PCT_TAM}"
assert TAM_ACCOUNTS == 91428, f"TAM account count drifted: {TAM_ACCOUNTS}"
assert SAM_ACCOUNTS == 20142, f"SAM account count drifted: {SAM_ACCOUNTS}"

SOM_ACQ_COST_CANONICAL = SOM_ACCOUNTS * CAC_CANONICAL
SOM_ACQ_COST_BENCHMARK = SOM_ACCOUNTS * CAC_BENCHMARK
SOM_ACQ_COST_DELTA = SOM_ACQ_COST_CANONICAL - SOM_ACQ_COST_BENCHMARK
SOM_SUPPORT_CANONICAL = SOM_ACCOUNTS * SUPPORT_CANONICAL
SOM_SUPPORT_BENCHMARK = SOM_ACCOUNTS * SUPPORT_BENCHMARK
SOM_SUPPORT_DELTA = SOM_SUPPORT_CANONICAL - SOM_SUPPORT_BENCHMARK
SOM_GROSS_PROFIT = SOM_ARR * GM_CANONICAL
ENTERPRISE_ACCOUNTS = SOM_ACCOUNTS * TIERS[3][2]
ENTERPRISE_CONCESSION = ENTERPRISE_ACCOUNTS * TIERS[3][1] * ENTERPRISE_CONCESSION_PCT
assert round(SOM_ACQ_COST_CANONICAL) == 2_016_000, \
    f"SOM acquisition cost drifted: {SOM_ACQ_COST_CANONICAL}"
assert round(SOM_ACQ_COST_DELTA) == 1_056_000, \
    f"SOM acquisition cost delta drifted: {SOM_ACQ_COST_DELTA}"
assert round(SOM_SUPPORT_CANONICAL) == 288_000, \
    f"SOM support cost drifted: {SOM_SUPPORT_CANONICAL}"
assert round(SOM_GROSS_PROFIT) == 1_166_400, \
    f"SOM gross profit drifted: {SOM_GROSS_PROFIT}"

PYTHON_SHARE_PCT = round(
    source_share(CANONICAL_REPO["lang_bytes"], CANONICAL_REPO["primary_language"]), 2)
SOURCE_BYTES_TOTAL = sum(CANONICAL_REPO["lang_bytes"].values())
GIT_SIZE_MIB = round(CANONICAL_REPO["git_size_kb"] / 1024, 1)


def derivation_rows():
    """Build the derivation trace: figure, expression, computed value."""
    rows = []
    rows.append(["Blended CAC (canonical)",
                 f"{COST_PER_TOUCH} USD/touch x {outbound_touches(CANONICAL_SIGNALS)}"
                 f" touches / {close_rate_at(CANONICAL_SIGNALS)} close",
                 round(CAC_CANONICAL, 2)])
    rows.append(["Blended CAC (benchmark)",
                 f"{COST_PER_TOUCH} USD/touch x {outbound_touches(BENCH_SIGNALS)}"
                 f" touches / {close_rate_at(BENCH_SIGNALS)} close",
                 round(CAC_BENCHMARK, 2)])
    rows.append(["Support COGS (canonical)",
                 f"{TICKETS_PER_ACCOUNT} tickets x {COST_PER_TICKET} USD x "
                 f"(1 - {DEFLECTION_PER_CHANNEL * CANONICAL_CHANNELS} deflection)",
                 round(SUPPORT_CANONICAL, 2)])
    rows.append(["Support COGS (retired basis)",
                 f"{TICKETS_PER_ACCOUNT} tickets x {COST_PER_TICKET} USD x "
                 f"(1 - {DEFLECTION_PER_CHANNEL * BENCH_CHANNELS} deflection)",
                 round(SUPPORT_BENCHMARK, 2)])
    rows.append(["Gross margin (canonical)",
                 f"({ACV} ACV - {COGS_CANONICAL} COGS) / {ACV}",
                 round(GM_CANONICAL * 100, 4)])
    rows.append(["Blended ACV",
                 "sum of tier ACV x tier share over the declared ladder",
                 round(ACV, 2)])
    rows.append(["3-yr LTV:CAC (Y1 cohort, canonical)",
                 f"{COHORT_ACCOUNTS} accounts x {round(GROSS_PROFIT_CANONICAL, 2)}"
                 f" GP x {round(GP_MULTIPLIER_3Y, 4)} / "
                 f"({COHORT_ACCOUNTS} accounts x {round(CAC_CANONICAL, 2)} CAC)",
                 round(LTVCAC_3Y_CANONICAL, 2)])
    rows.append(["SOM exit ARR", f"{SOM_ACCOUNTS} accounts x {ACV} ACV", SOM_ARR])
    rows.append(["SOM acquisition cost delta",
                 f"({SOM_ACCOUNTS} x {round(CAC_CANONICAL, 2)}) - "
                 f"({SOM_ACCOUNTS} x {round(CAC_BENCHMARK, 2)})",
                 round(SOM_ACQ_COST_DELTA)])
    rows.append(["TAM accounts", f"{TAM_USD} / {ACV}", TAM_ACCOUNTS])
    rows.append(["SAM accounts", f"{SAM_USD} / {ACV}", SAM_ACCOUNTS])
    rows.append(["SOM share of SAM (pct)",
                 f"100 x {SOM_ARR} / {SAM_USD}",
                 round(SOM_PCT_SAM, 4)])
    return rows


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def q(v):
    s = str(v)
    return '"' + s.replace('"', '""') + '"' if any(c in s for c in ',"\n') else s


def block(title, header, rows):
    lines = [f"### {title}", ",".join(header)]
    lines += [",".join(q(c) for c in r) for r in rows]
    return "\n".join(lines)


out = {
    "as_of": AS_OF, "as_of_ts": AS_OF_TS,
    "repo": CANONICAL_REPO, "retired": RETIRED_BASIS,
    "canonical_install": CANONICAL_INSTALL,
    "canonical_signals": CANONICAL_SIGNALS,
    "canonical_community_channels": CANONICAL_CHANNELS,
    "tiers": [{"tier": t, "acv_usd": p, "share": s, "weighted_usd": round(p * s, 2)}
              for t, p, s in TIERS],
    "unit_econ": {
        "blended_acv": ACV, "cogs_legacy": COGS_BENCHMARK,
        "hosting_cogs": HOSTING_COST_PER_ACCOUNT,
        "support_legacy": SUPPORT_BENCHMARK, "support_canonical": SUPPORT_CANONICAL,
        "cogs_canonical": COGS_CANONICAL,
        "gm_legacy_pct": round(GM_BENCHMARK * 100, 2),
        "gm_canonical_pct": round(GM_CANONICAL * 100, 2),
        "gm_delta_pts": round((GM_CANONICAL - GM_BENCHMARK) * 100, 2),
        "gp_per_acct": round(GROSS_PROFIT_CANONICAL, 2),
        "gp_per_acct_legacy": round(GROSS_PROFIT_BENCHMARK, 2),
        "cac_now": round(CAC_CANONICAL, 2), "cac_bench": round(CAC_BENCHMARK, 2),
        "cac_delta": round(CAC_CANONICAL - CAC_BENCHMARK, 2),
        "payback_now_yr": round(PAYBACK_CANONICAL, 2),
        "payback_bench_yr": round(PAYBACK_BENCHMARK, 2),
        "payback_delta_yr": round(PAYBACK_CANONICAL - PAYBACK_BENCHMARK, 2),
        "life_yr": round(LIFE_YEARS, 2), "ltv_full": round(LTV_FULL),
        "ltv_cac_full": round(LTV_CAC_FULL, 2),
        "nrr_pct": round(NRR * 100), "mult_3y": round(GP_MULTIPLIER_3Y, 4),
        "ltvcac_3y_now": round(LTVCAC_3Y_CANONICAL, 2),
        "ltvcac_3y_bench": round(LTVCAC_3Y_BENCHMARK, 2),
        "ltvcac_3y_delta": round(LTVCAC_3Y_CANONICAL - LTVCAC_3Y_BENCHMARK, 2),
    },
    "som": {
        "accounts": SOM_ACCOUNTS, "arr": SOM_ARR,
        "cac_now": round(SOM_ACQ_COST_CANONICAL),
        "cac_bench": round(SOM_ACQ_COST_BENCHMARK),
        "cac_delta": round(SOM_ACQ_COST_DELTA),
        "support_now": round(SOM_SUPPORT_CANONICAL),
        "support_bench": round(SOM_SUPPORT_BENCHMARK),
        "support_delta": round(SOM_SUPPORT_DELTA),
        "gross_profit": round(SOM_GROSS_PROFIT),
        "ent_accounts": round(ENTERPRISE_ACCOUNTS, 1),
        "ent_concession": round(ENTERPRISE_CONCESSION),
    },
    "market": {
        "tam": TAM_USD, "tam_accts": TAM_ACCOUNTS, "sam": SAM_USD,
        "sam_accts": SAM_ACCOUNTS, "som": SOM_ARR,
        "sam_pct_tam": round(SAM_PCT_TAM, 2),
        "som_pct_sam": round(SOM_PCT_SAM, 2),
        "som_pct_tam": round(SOM_PCT_TAM, 2),
        "plg_share_pct": round(SELF_SERVE_SHARE * 100),
        "plg_sam": SELF_SERVE_USD, "plg_accts": SELF_SERVE_ACCOUNTS,
        "sales_share_pct": round(SALES_LED_SHARE * 100), "sales_sam": SALES_LED_USD,
        "sales_accts": SALES_LED_ACCOUNTS,
        "som_pct_sales_sam": round(SOM_PCT_SALES_LED, 2),
    },
    "revenue": [{"year": y, "accounts": a, "exit_arr": a * ACV,
                 "recognized": round(a * ACV * RECOGNITION_FACTOR)}
                for y, a in RAMP],
    "benchmarks": {"direct_hit": 1.000, "multi_hop_hit": 0.800,
                   "adversarial_hit": 0.000, "leak_rate": 0.000,
                   "locomo": None, "longmemeval": None},
    "deployment": {
        "sidney": "216.198.115.91:2222",
        "gabe_route": "the finance model is gated and published through gabe on sidney",
        "live_path": "/opt/mem20/live/compute_model.py",
    },
    "derivation": [{"figure": f, "expression": e, "value": v}
                   for f, e, v in derivation_rows()],
    "repo_metrics": {"python_share_pct": PYTHON_SHARE_PCT,
                     "source_bytes_total": SOURCE_BYTES_TOTAL,
                     "git_size_mib": GIT_SIZE_MIB},
}

csv_blocks = []
csv_blocks.append(block("corrections_register.csv",
    ["id", "item", "legacy_value", "canonical_value", "change", "source"], [
    ["C-01", "Canonical repository URL",
     RETIRED_BASIS["retired_url"] + " (404)", CANONICAL_REPO["url"] + " (public)",
     "REPLACED", "GitHub API"],
    ["C-02", "Default branch", "main (unpublished)", "main (published)",
     "CONFIRMED", "GitHub API"],
    ["C-03", "As-of commit", "none",
     f"{CANONICAL_REPO['head_short']} ({CANONICAL_REPO['head_date']})",
     "ADDED", "GitHub API"],
    ["C-04", "Prior commit", "none",
     f"{CANONICAL_REPO['parent_short']} ({CANONICAL_REPO['parent_date']})",
     "ADDED", "GitHub API"],
    ["C-05", "License", "MIT", "MIT (SPDX: MIT)", "UNCHANGED", "GitHub API"],
    ["C-06", "Repository size (git-reported)", "n/a",
     f"{CANONICAL_REPO['git_size_kb']} KB ({GIT_SIZE_MIB} MiB)", "ADDED", "GitHub API"],
    ["C-07", "Working tree", "n/a", f"{CANONICAL_REPO['worktree_mb']} MB",
     "ADDED", "Upstream publication audit"],
    ["C-08", "Tracked files", "n/a", CANONICAL_REPO["tracked_files"],
     "ADDED", "Upstream publication audit"],
    ["C-09", "Subsystems", "n/a", CANONICAL_REPO["subsystems"],
     "ADDED", "Upstream publication audit"],
    ["C-10", "Tools", "257-260", CANONICAL_REPO["tools"],
     "RECONCILED to house figure", "House model"],
    ["C-11", "Domains", "26", CANONICAL_REPO["domains"], "UNCHANGED", "House model"],
    ["C-12", "Stars", "unknown (traction assumed)", CANONICAL_REPO["stars"],
     "REFRESHED", "GitHub API"],
    ["C-13", "Forks", "unknown", CANONICAL_REPO["forks"], "REFRESHED", "GitHub API"],
    ["C-14", "Watchers", "unknown", CANONICAL_REPO["watchers"],
     "REFRESHED", "GitHub API"],
    ["C-15", "Open issues", "unknown", CANONICAL_REPO["open_issues"],
     "REFRESHED", "GitHub API"],
    ["C-16", "Published releases", RETIRED_BASIS["retired_version_string"],
     CANONICAL_REPO["releases"], "REFRESHED", "GitHub API"],
    ["C-17", "Issue tracker", "assumed available",
     f"disabled (has_issues={CANONICAL_REPO['has_issues']})", "REFRESHED", "GitHub API"],
    ["C-18", "Discussions", "assumed available",
     f"disabled (has_discussions={CANONICAL_REPO['has_discussions']})",
     "REFRESHED", "GitHub API"],
    ["C-19", "Package index entry", "assumed published",
     f"absent (on_package_index={CANONICAL_REPO['on_package_index']})",
     "REFRESHED", "GitHub API"],
    ["C-20", "Wiki", "n/a",
     f"enabled (has_wiki={CANONICAL_REPO['has_wiki']})", "ADDED", "GitHub API"],
    ["C-21", "Contributors", "n/a", CANONICAL_REPO["contributors"],
     "ADDED", "GitHub API"],
    ["C-22", "Primary language", "Python",
     f"Python ({PYTHON_SHARE_PCT}% of source)", "CONFIRMED", "GitHub API"],
    ["C-23", "Source volume", "n/a", f"{SOURCE_BYTES_TOTAL:,} bytes",
     "ADDED", "GitHub API"],
    ["C-24", "Repository age", "n/a",
     f"{CANONICAL_REPO['repo_age_days']} days (created {CANONICAL_REPO['created_at']})",
     "ADDED", "GitHub API"],
    ["C-25", "Install path",
     RETIRED_BASIS["retired_install"] + " (not on PyPI)", CANONICAL_INSTALL,
     "REPLACED", "Upstream audit"],
    ["C-26", "Retired source",
     f"{RETIRED_BASIS['retired_source']}", "retired", "RETIRED", "Upstream audit"],
]))

csv_blocks.append(block("repo_dependencies.csv",
    ["id", "finance_line", "repo_signal", "legacy_value", "canonical_value",
     "delta", "impact"], [
    ["D-01", "SOM self-serve component", "Community traction (stars/forks)",
     "36 of 120 accounts", "0 of 120 accounts", "-36 accounts",
     "Self-serve revenue line eliminated at the canonical state"],
    ["D-02", "Blended CAC", "Inbound volume (stars / releases / package)",
     round(CAC_BENCHMARK, 2), round(CAC_CANONICAL, 2),
     f"+{round(CAC_CANONICAL - CAC_BENCHMARK, 2)}",
     "No inbound signal: the low-cost OSS acquisition path is absent"],
    ["D-03", "CAC payback", "Derived from D-02",
     round(PAYBACK_BENCHMARK, 2), round(PAYBACK_CANONICAL, 2),
     f"+{round(PAYBACK_CANONICAL - PAYBACK_BENCHMARK, 2)} yr",
     "Payback crosses the 12-month operating threshold"],
    ["D-04", "SOM acquisition cost", "Derived from D-02",
     round(SOM_ACQ_COST_BENCHMARK), round(SOM_ACQ_COST_CANONICAL),
     f"+{round(SOM_ACQ_COST_DELTA)}",
     "Full SOM book costs 1,056,000 USD more to acquire"],
    ["D-05", "Support cost per account", "Issue tracker / discussions",
     round(SUPPORT_BENCHMARK, 2), round(SUPPORT_CANONICAL, 2),
     f"+{round(SUPPORT_CANONICAL - SUPPORT_BENCHMARK, 2)}",
     "No community deflection channel at the canonical state"],
    ["D-06", "SOM annual support cost", "Derived from D-05",
     round(SOM_SUPPORT_BENCHMARK), round(SOM_SUPPORT_CANONICAL),
     f"+{round(SOM_SUPPORT_DELTA)}", "Annual support line doubles"],
    ["D-07", "Gross margin", "Derived from D-05",
     f"{round(GM_BENCHMARK * 100, 1)}%", f"{round(GM_CANONICAL * 100, 1)}%",
     f"{round((GM_CANONICAL - GM_BENCHMARK) * 100, 1)} pts",
     "Support cost increase compresses gross margin"],
    ["D-08", "License revenue", "License (MIT)", 0, 0, "0",
     "MIT grants self-host rights: no license monetisation surface"],
    ["D-09", "Enterprise concession", "Bus factor (contributor count)", "0%",
     f"{round(ENTERPRISE_CONCESSION_PCT * 100)}%", "-8%",
     f"{CANONICAL_REPO['contributors']} contributors; procurement prices "
     "concentration risk"],
    ["D-10", "3-yr LTV:CAC (Y1 cohort)", "Derived from D-02 / D-07",
     round(LTVCAC_3Y_BENCHMARK, 2), round(LTVCAC_3Y_CANONICAL, 2),
     f"{round(LTVCAC_3Y_CANONICAL - LTVCAC_3Y_BENCHMARK, 2)}x",
     "Falls below the 3x institutional hurdle"],
    ["D-11", "Published releases", "Release artefacts", "unknown",
     CANONICAL_REPO["releases"], "-", "No GitHub release: maturity signal absent"],
    ["D-12", "As-of commit", "Repository HEAD", "n/a",
     CANONICAL_REPO["head_short"], "n/a", f"Finance model as-of {AS_OF_TS}"],
    ["D-13", "Install path", "Package distribution",
     RETIRED_BASIS["retired_install"], "git+https install", "-",
     "Adds install friction at the top of the self-serve funnel"],
    ["D-14", "Time-to-first-value", "Derived from D-13", "1 day", "3-5 days",
     "+2-4 days", "Delays self-serve activation and conversion"],
]))

ue_rows = [["Blended ACV", ACV, "USD/account/yr",
            "Tier mix 72/12/12/4 on 6K/18K/36K/80K - reconciles exactly"]]
for _tier_name, _tier_price, _tier_share in TIERS:
    ue_rows.append([f"{_tier_name} tier ACV", _tier_price, "USD/account/yr",
                    f"{round(_tier_share * 100)}% of paying accounts"])
ue_rows += [
    ["Hosting COGS", HOSTING_COST_PER_ACCOUNT, "USD/account/yr",
     "Retained from the prior COGS structure"],
    ["Support COGS (canonical)", round(SUPPORT_CANONICAL, 2), "USD/account/yr",
     "Direct support; no community deflection"],
    ["Support COGS (retired basis)", round(SUPPORT_BENCHMARK, 2), "USD/account/yr",
     "Community-deflected assumption"],
    ["Total COGS (canonical)", round(COGS_CANONICAL, 2), "USD/account/yr",
     "Hosting + direct support"],
    ["Gross margin (retired basis)", round(GM_BENCHMARK * 100, 1), "%", "Derived"],
    ["Gross margin (canonical)", round(GM_CANONICAL * 100, 1), "%", "Derived"],
    ["Gross profit per account", round(GROSS_PROFIT_CANONICAL, 2), "USD/account/yr",
     "Derived"],
    ["Blended CAC (canonical)", round(CAC_CANONICAL, 2), "USD",
     "Derived from the canonical repository state"],
    ["Blended CAC (benchmark)", round(CAC_BENCHMARK, 2), "USD",
     "Derived from the retired-basis assumptions"],
    ["CAC payback (canonical)", round(PAYBACK_CANONICAL, 2), "years", "Derived"],
    ["CAC payback (benchmark)", round(PAYBACK_BENCHMARK, 2), "years", "Derived"],
    ["Logo churn", round(CHURN * 100, 1), "%", "House assumption"],
    ["Average account life", round(LIFE_YEARS, 2), "years", "1 / churn"],
    ["LTV (gross profit, full life)", round(LTV_FULL), "USD", "Derived"],
    ["LTV:CAC (full life)", round(LTV_CAC_FULL, 2), "x", "Derived"],
    ["NRR", round(NRR * 100), "%", "House assumption"],
    ["3-yr GP multiplier (NRR-compounded)", round(GP_MULTIPLIER_3Y, 4), "x",
     "1 + NRR + NRR^2"],
    ["3-yr LTV:CAC (Y1 cohort, benchmark)", round(LTVCAC_3Y_BENCHMARK, 2), "x",
     "Derived"],
    ["3-yr LTV:CAC (Y1 cohort, canonical)", round(LTVCAC_3Y_CANONICAL, 2), "x",
     "Derived; below the 3x hurdle"],
    ["SOM accounts (3-yr obtainable)", SOM_ACCOUNTS, "accounts", "House SOM / ACV"],
    ["SOM exit ARR", SOM_ARR, "USD", f"{SOM_ACCOUNTS} x {ACV}"],
    ["SOM gross profit (annual)", round(SOM_GROSS_PROFIT), "USD",
     "SOM ARR x canonical GM"],
    ["SOM acquisition cost (canonical)", round(SOM_ACQ_COST_CANONICAL), "USD",
     f"{SOM_ACCOUNTS} x {round(CAC_CANONICAL, 2)}"],
    ["SOM acquisition cost (benchmark)", round(SOM_ACQ_COST_BENCHMARK), "USD",
     f"{SOM_ACCOUNTS} x {round(CAC_BENCHMARK, 2)}"],
    ["SOM acquisition cost delta", round(SOM_ACQ_COST_DELTA), "USD",
     "Repo-state driven"],
]
for _ramp_year, _ramp_accounts in RAMP:
    ue_rows.append([f"Year {_ramp_year} accounts", _ramp_accounts, "accounts",
                    "Ramp" if _ramp_year < 3 else "= SOM"])
    ue_rows.append([f"Year {_ramp_year} exit ARR", _ramp_accounts * ACV, "USD",
                    f"{_ramp_accounts} x {ACV}"])
csv_blocks.append(block("unit_economics.csv", ["metric", "value", "unit", "basis"],
                        ue_rows))

csv_blocks.append(block("market_sizing.csv",
    ["layer", "value_usd", "accounts", "share_of_parent", "notes"], [
    ["TAM (agent memory infrastructure)", TAM_USD, TAM_ACCOUNTS, "",
     f"Bottom-up: {TAM_ACCOUNTS:,} addressable buying units x {ACV} blended ACV"],
    ["SAM (serviceable addressable)", SAM_USD, SAM_ACCOUNTS,
     f"{round(SAM_PCT_TAM, 2)}% of TAM",
     "Reachable product surface: MCP/Python, NA+EU, self-host-first"],
    ["  self-serve slice of SAM", int(SELF_SERVE_USD), SELF_SERVE_ACCOUNTS,
     f"{round(SELF_SERVE_SHARE * 100)}% of SAM",
     "Gated on published releases and package availability"],
    ["  sales-led slice of SAM", int(SALES_LED_USD), SALES_LED_ACCOUNTS,
     f"{round(SALES_LED_SHARE * 100)}% of SAM",
     "Reachable via the direct motion"],
    ["SOM (3-yr obtainable)", SOM_ARR, SOM_ACCOUNTS,
     f"{round(SOM_PCT_SAM, 1)}% of SAM",
     f"{SOM_ACCOUNTS} accounts x {ACV} = {SOM_ARR} ARR; "
     f"{round(SOM_PCT_TAM, 2)}% of TAM"],
    ["SOM vs sales-led SAM", SOM_ARR, SOM_ACCOUNTS,
     f"{round(SOM_PCT_SALES_LED, 2)}% of sales-led SAM",
     "Penetration required with the self-serve path unavailable"],
]))

csv_blocks.append(block("derivation_trace.csv",
    ["figure", "expression", "computed_value"], derivation_rows()))

print("=== mem20-finance-model.json ===")
print(json.dumps(out, indent=2, default=str))
print()
print("=== mem20-finance-model.csv-blocks ===")
print("\n\n".join(csv_blocks))
