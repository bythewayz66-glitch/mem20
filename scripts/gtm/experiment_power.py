#!/usr/bin/env python3
"""Sample-size and power calculator for mem20 growth experiment GH-EXP-001.

Why this exists
---------------
The experiment brief at ``docs/gtm/experiment-gh-exp-001-prove-it-hero.md``
pre-registers a sample size. A pre-registered number that nobody can reproduce
is a guess with a citation, so the arithmetic lives here and the brief quotes
this script's output verbatim.

The primary metric is a **count of discrete events in a fixed window** (unique
repository views, GitHub stars gained). Counts of rare events are Poisson, not
normal, so the sample size comes from an exact one-sided Poisson test rather
than a t-test. That choice is not decoration: the measured baseline is about one
star per fourteen days, where a normal approximation is simply wrong.

Dependency-free: the Poisson CDF is built from the regularised incomplete gamma
function (series for small x, continued fraction for large x), so this runs on a
bare python3 with no pip install.

Usage
-----
    python3 scripts/gtm/experiment_power.py
    python3 scripts/gtm/experiment_power.py --json
    python3 scripts/gtm/experiment_power.py --self-test
    python3 scripts/gtm/experiment_power.py --stars 3 --age-days 41 --views-per-day 0.71

Exit codes: 0 = ok, 1 = self-test failure, 2 = bad arguments.
"""
from __future__ import annotations

import argparse
import json
import math
import sys

# Pre-registered test parameters. These are fixed before the experiment runs and
# are not to be tuned after seeing data.
ALPHA = 0.05
POWER = 0.80

# Measured baselines, with their provenance. Overridable on the command line so
# the table can be recomputed when the counters move.
#   stars      : GitHub API repos/bythewayz66-glitch/mem20 -> stargazers_count
#   age_days   : repo created_at 2026-10-06 -> measured 2026-11-16
#   views/day  : GitHub traffic/views, 14-day window ending 2026-10-31,
#                daily unique mean 0.71, sd 0.83 (docs/gtm/launch-instrumentation.md)
DEFAULT_STARS = 3
DEFAULT_AGE_DAYS = 41
DEFAULT_VIEWS_PER_DAY = 0.71
DEFAULT_VIEWS_SD = 0.83

# The window the brief pre-registers for the primary read.
PRIMARY_WINDOW_DAYS = 14

# Effect sizes the brief commits to detecting.
MDES = (2.0, 3.0, 5.0)


# --------------------------------------------------------------------------
# Exact Poisson machinery
# --------------------------------------------------------------------------
def _gser(a: float, x: float) -> float:
    """Regularised lower incomplete gamma P(a, x) by series (x < a + 1)."""
    itmax, eps = 10000, 3e-16
    ap = a
    total = 1.0 / a
    delta = total
    for _ in range(itmax):
        ap += 1.0
        delta *= x / ap
        total += delta
        if abs(delta) < abs(total) * eps:
            break
    return total * math.exp(-x + a * math.log(x) - math.lgamma(a))


def _gcf(a: float, x: float) -> float:
    """Regularised upper incomplete gamma Q(a, x) by continued fraction."""
    itmax, eps, fpmin = 10000, 3e-16, 1e-300
    b = x + 1.0 - a
    c = 1.0 / fpmin
    d = 1.0 / b
    h = d
    for i in range(1, itmax + 1):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < fpmin:
            d = fpmin
        c = b + an / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def poisson_cdf(k: int, lam: float) -> float:
    """P(X <= k) for X ~ Poisson(lam)."""
    if k < 0:
        return 0.0
    if lam <= 0.0:
        return 1.0
    # P(X <= k) = Q(k+1, lam), the regularised UPPER incomplete gamma.
    # The continued fraction converges for x > a + 1, the series for x < a + 1.
    if lam > k + 2.0:
        return _gcf(k + 1.0, lam)
    return 1.0 - _gser(k + 1.0, lam)


def poisson_sf(k: int, lam: float) -> float:
    """P(X >= k) for X ~ Poisson(lam)."""
    return 1.0 - poisson_cdf(k - 1, lam)


def critical_value(lam0: float, alpha: float = ALPHA) -> int:
    """Smallest integer k with P(X >= k | lam0) <= alpha."""
    k = 0
    while poisson_sf(k, lam0) > alpha:
        k += 1
        if k > 10_000_000:
            raise RuntimeError("no critical value found")
    return k


def power_at(rate_per_day: float, mde: float, days: int, alpha: float = ALPHA) -> dict:
    """Power of the exact one-sided test at a fixed window length."""
    lam0 = rate_per_day * days
    k = critical_value(lam0, alpha)
    lam1 = mde * lam0
    return {
        "days": days,
        "lam0": lam0,
        "lam1": lam1,
        "critical_k": k,
        "power": poisson_sf(k, lam1),
    }


def required_window_days(
    rate_per_day: float, mde: float, alpha: float = ALPHA, power: float = POWER,
    max_days: int = 3650,
) -> dict | None:
    """Smallest whole-day window whose exact test reaches the target power."""
    for days in range(1, max_days + 1):
        row = power_at(rate_per_day, mde, days, alpha)
        if row["power"] >= power:
            return row
    return None


# --------------------------------------------------------------------------
# Switchback design
# --------------------------------------------------------------------------
# The page is static and carries no analytics snippet, so there is no per-visitor
# randomisation available. The only randomisation the stack can actually execute
# is a DAY-LEVEL SWITCHBACK: on each day the live page serves one arm, and the
# arm is assigned by a pre-committed coin flip. That is a real randomised
# experiment, and it is the design the brief pre-registers.
#
# Its cost is that the unit of randomisation is the day, so the effective sample
# size is the number of DAYS, not the number of visitors. With a measured daily
# view sd of 0.83 against a mean of 0.71, day-to-day variance is the binding
# constraint, and the honest answer is that a 14-day switchback cannot detect a
# 2x lift on views. The table below says so instead of hiding it.
SWITCHBACK_DAYS = (14, 28, 56)


def switchback_table(views_per_day: float, views_sd: float) -> list[dict]:
    """Power of a day-level switchback at several window lengths.

    Uses a two-sample normal approximation on the DAILY counts, which is the
    right model here: the day is the randomisation unit, so the relevant
    variance is the between-day variance, and with ~7 days per arm the normal
    approximation on the arm means is adequate. The Poisson table above is the
    right model for a single-arm count read; this one is the right model for a
    two-arm comparison. Both are reported because they answer different
    questions.
    """
    from math import sqrt

    z_alpha = 1.6448536269514722  # one-sided 0.05
    z_beta = 0.8416212335729143  # power 0.80
    rows = []
    for days in SWITCHBACK_DAYS:
        per_arm = days / 2.0
        se_unit = views_sd * sqrt(2.0 / per_arm) if per_arm else float("inf")
        # smallest absolute lift detectable at the target power
        mde_abs = (z_alpha + z_beta) * se_unit
        mde_rel = mde_abs / views_per_day if views_per_day else float("inf")
        rows.append(
            {
                "days": days,
                "days_per_arm": per_arm,
                "se_of_difference": se_unit,
                "mde_absolute_views_per_day": mde_abs,
                "mde_relative": mde_rel,
                "detects_2x": mde_rel <= 2.0,
            }
        )
    return rows


def traffic_for_switchback(days: int, target_mde_rel: float) -> dict:
    """Mean daily views needed for a switchback to detect ``target_mde_rel``.

    The switchback's detectable lift depends on the coefficient of variation of
    the daily counts, not on their level. Under a Poisson model the CV is
    ``1/sqrt(mean)``, so raising traffic is exactly what buys sensitivity. This
    function inverts the relation and answers the only question that matters
    before committing 56 days: *how much traffic does this design need?*
    """
    from math import sqrt

    z_alpha = 1.6448536269514722
    z_beta = 0.8416212335729143
    per_arm = days / 2.0
    cv_measured = DEFAULT_VIEWS_SD / DEFAULT_VIEWS_PER_DAY
    cv_poisson = 1.0 / sqrt(DEFAULT_VIEWS_PER_DAY)

    # mde_rel = (z_a + z_b) * CV * sqrt(2 / per_arm)
    # => mean = ((z_a + z_b) * CV * sqrt(2 / per_arm) / mde_rel) ** 2
    def _mean(cv: float) -> float:
        return ((z_alpha + z_beta) * cv * sqrt(2.0 / per_arm) / target_mde_rel) ** 2

    required_measured = _mean(cv_measured)
    required_poisson = _mean(cv_poisson)
    return {
        "days": days,
        "days_per_arm": per_arm,
        "target_mde_rel": target_mde_rel,
        "cv_measured": cv_measured,
        "cv_poisson": cv_poisson,
        "required_views_per_day": required_measured,
        "required_views_per_day_poisson": required_poisson,
        "baseline_views_per_day": DEFAULT_VIEWS_PER_DAY,
        "traffic_multiple_needed": required_measured / DEFAULT_VIEWS_PER_DAY,
    }


def render_traffic_requirement(rows: list[dict]) -> str:
    out = []
    out.append("traffic precondition - mean unique views/day needed to detect a lift")
    out.append(
        f"{'window':>8}{'target lift':>13}{'views/day (meas)':>18}"
        f"{'views/day (Pois)':>18}{'x baseline':>12}"
    )
    out.append("-" * 69)
    for r in rows:
        out.append(
            f"{r['days']:>8}{r['target_mde_rel']:>12.2f}x"
            f"{r['required_views_per_day']:>18.2f}"
            f"{r['required_views_per_day_poisson']:>18.2f}"
            f"{r['traffic_multiple_needed']:>12.1f}"
        )
    out.append("")
    out.append(
        f"measured baseline: {DEFAULT_VIEWS_PER_DAY:.2f} unique views/day "
        f"(14-day window ending 2026-10-31)"
    )
    out.append(
        f"CV measured {rows[0]['cv_measured']:.2f} vs Poisson {rows[0]['cv_poisson']:.2f} "
        "- the two models agree, so the Poisson table is not a convenience."
    )
    out.append("")
    return "\n".join(out)


def page_share_sensitivity(total_lift: float, shares: tuple[float, ...] = (1.0, 0.5, 0.25, 0.10)) -> list[dict]:
    """Page-level lift required to produce ``total_lift`` on repo views.

    The primary metric is unique repo views per day, but the page is only one of
    several ways a person reaches the repo. If the page accounts for a share
    ``s`` of those views, a page-level multiplier ``m`` shows up on the total as
    ``m*s + (1 - s)``. Inverting that gives the page-level lift the treatment
    must actually deliver for the experiment to see ``total_lift``:

        m = (total_lift - 1 + s) / s

    This is the single most important caveat in the design, so it is a table
    rather than a sentence: at a 10% page share, a 1.55x total read requires a
    6.50x page-level effect, which no hero rewrite will produce.
    """
    rows = []
    for s in shares:
        rows.append(
            {
                "page_share": s,
                "total_lift": total_lift,
                "required_page_lift": (total_lift - 1.0 + s) / s,
            }
        )
    return rows


def render_page_share(rows: list[dict]) -> str:
    out = []
    out.append("attribution sensitivity - page-level lift needed for the total read")
    out.append(f"{'page share of repo views':>26}{'total lift':>12}{'page lift needed':>18}")
    out.append("-" * 56)
    for r in rows:
        out.append(
            f"{r['page_share'] * 100:>25.0f}%{r['total_lift']:>11.2f}x"
            f"{r['required_page_lift']:>17.2f}x"
        )
    out.append("")
    out.append("The page share is NOT measurable today (traffic/referrers is 404).")
    out.append("Treat this table as the reason the experiment is a screen, not a verdict.")
    out.append("")
    return "\n".join(out)


def permutation_p_value(
    arm_a: list[float], arm_b: list[float], iterations: int = 20000, seed: int = 20261116
) -> dict:
    """One-sided permutation test on the difference of arm means.

    This is the CONFIRMATORY test for GH-EXP-001. It makes no distributional
    assumption, which matters because the daily counts are small and roughly
    Poisson. The day label is the randomisation, so permuting the labels is the
    correct null: it asks how often a difference this large arises when the arm
    assignment carried no information.

    The seed is fixed so the p-value is reproducible; the Monte-Carlo error at
    20,000 iterations is well below the resolution anyone will report.
    """
    import random

    a = [float(x) for x in arm_a]
    b = [float(x) for x in arm_b]
    if not a or not b:
        raise ValueError("both arms need at least one day")

    mean_a = sum(a) / len(a)
    mean_b = sum(b) / len(b)
    observed = mean_b - mean_a
    pooled = a + b
    n_a = len(a)
    rng = random.Random(seed)

    at_least = 0
    for _ in range(iterations):
        rng.shuffle(pooled)
        diff = sum(pooled[n_a:]) / (len(pooled) - n_a) - sum(pooled[:n_a]) / n_a
        if diff >= observed:
            at_least += 1

    return {
        "n_a": len(a),
        "n_b": len(b),
        "mean_a": mean_a,
        "mean_b": mean_b,
        "observed_difference": observed,
        "lift_multiple": (mean_b / mean_a) if mean_a else float("inf"),
        "iterations": iterations,
        "p_value": (at_least + 1) / (iterations + 1),
        "seed": seed,
    }


def render_analysis(result: dict) -> str:
    out = []
    out.append("GH-EXP-001 confirmatory read - one-sided permutation test")
    out.append(
        f"arm A: {result['n_a']} day(s), mean {result['mean_a']:.2f} unique views/day"
    )
    out.append(
        f"arm B: {result['n_b']} day(s), mean {result['mean_b']:.2f} unique views/day"
    )
    out.append(f"observed difference (B - A): {result['observed_difference']:.2f}")
    out.append(f"lift as a multiple of A      : {result['lift_multiple']:.2f}x")
    out.append(
        f"p-value (one-sided, {result['iterations']} permutations, seed {result['seed']}): "
        f"{result['p_value']:.3f}"
    )
    out.append("")
    out.append("Reject the null at alpha 0.05 only if p <= 0.05.")
    out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------
def build_table(stars: int, age_days: int, views_per_day: float, views_sd: float) -> dict:
    star_rate = stars / age_days if age_days else 0.0
    dispersion = (views_sd ** 2) / views_per_day if views_per_day else float("nan")

    metrics = [
        ("unique_repo_views_per_day", views_per_day, "views"),
        ("stars_per_day", star_rate, "stars"),
    ]

    rows = []
    for name, rate, unit in metrics:
        for mde in MDES:
            at_primary = power_at(rate, mde, PRIMARY_WINDOW_DAYS)
            needed = required_window_days(rate, mde)
            rows.append(
                {
                    "metric": name,
                    "unit": unit,
                    "mde": mde,
                    "rate_per_day": rate,
                    "primary_window_days": PRIMARY_WINDOW_DAYS,
                    "lam0_at_primary": at_primary["lam0"],
                    "lam1_at_primary": at_primary["lam1"],
                    "critical_k_at_primary": at_primary["critical_k"],
                    "power_at_primary": at_primary["power"],
                    "days_for_target_power": needed["days"] if needed else None,
                    "lam0_at_target": needed["lam0"] if needed else None,
                    "lam1_at_target": needed["lam1"] if needed else None,
                    "critical_k_at_target": needed["critical_k"] if needed else None,
                }
            )

    return {
        "experiment": "GH-EXP-001",
        "alpha": ALPHA,
        "power": POWER,
        "sided": "one-sided",
        "test": "exact Poisson",
        "primary_window_days": PRIMARY_WINDOW_DAYS,
        "switchback": switchback_table(views_per_day, views_sd),
        "traffic_requirement": [
            traffic_for_switchback(d, m) for d in SWITCHBACK_DAYS for m in (2.0, 3.0)
        ],
        "page_share_sensitivity": page_share_sensitivity(1.55),
        "baseline": {
            "stars_total": stars,
            "repo_age_days": age_days,
            "stars_per_day": star_rate,
            "views_per_day": views_per_day,
            "views_sd": views_sd,
            "views_variance_over_mean": dispersion,
        },
        "rows": rows,
    }


def render(report: dict) -> str:
    b = report["baseline"]
    out = []
    out.append("mem20 growth experiment GH-EXP-001 - pre-registered sample size")
    out.append(
        f"test: {report['test']}, {report['sided']}, alpha = {report['alpha']}, "
        f"power = {report['power']}"
    )
    out.append("")
    out.append(
        f"baseline stars        : {b['stars_total']} over {b['repo_age_days']} days "
        f"= {b['stars_per_day']:.2f} stars/day"
    )
    out.append(
        f"baseline unique views : {b['views_per_day']:.2f} /day "
        f"(sd {b['views_sd']:.2f}, variance/mean = {b['views_variance_over_mean']:.2f})"
    )
    out.append(
        "  variance/mean ~ 1 is the measured justification for the Poisson model;"
    )
    out.append(
        "  a normal approximation is not used anywhere in this table."
    )
    out.append("")
    header = (
        f"{'metric':<26}{'MDE':>5}{'k*':>5}{'lam0':>9}{'lam1':>9}"
        f"{'power@14d':>11}{'days needed':>13}"
    )
    out.append(header)
    out.append("-" * len(header))
    for r in report["rows"]:
        days = r["days_for_target_power"]
        out.append(
            f"{r['metric']:<26}{r['mde']:>4.0f}x{r['critical_k_at_primary']:>5}"
            f"{r['lam0_at_primary']:>9.2f}{r['lam1_at_primary']:>9.2f}"
            f"{r['power_at_primary']:>11.2f}{(str(days) if days else 'n/a'):>13}"
        )
    out.append("")
    out.append("k* = smallest count that rejects the baseline at alpha (one-sided).")
    out.append("lam0 / lam1 = expected event counts in the 14-day primary window.")
    out.append("power@14d = exact power of the 14-day read at that MDE.")
    out.append("days needed = shortest window reaching power 0.80 at that MDE.")
    out.append("")
    out.append("day-level switchback (two-arm, normal approximation on daily counts)")
    out.append(
        f"{'window':>8}{'days/arm':>10}{'SE(diff)':>11}{'MDE abs':>10}{'MDE rel':>10}{'detects 2x':>12}"
    )
    out.append("-" * 61)
    for r in report["switchback"]:
        out.append(
            f"{r['days']:>8}{r['days_per_arm']:>10.0f}{r['se_of_difference']:>11.2f}"
            f"{r['mde_absolute_views_per_day']:>10.2f}{r['mde_relative']:>10.2f}"
            f"{('yes' if r['detects_2x'] else 'no'):>12}"
        )
    out.append("")
    out.append("MDE rel = smallest detectable lift as a multiple of the baseline mean.")
    out.append("A 14-day switchback detects a 1.55x lift; 56 days detects 0.78x.")
    out.append("")
    out.append(render_traffic_requirement(report["traffic_requirement"]))
    out.append(render_page_share(report["page_share_sensitivity"]))
    return "\n".join(out)


def self_test() -> int:
    # Reference values computed independently by direct summation of the
    # Poisson pmf (see the brief's reproduction section), not by this module.
    checks = [
        ("P(X<=2 | 1.024)", poisson_cdf(2, 1.024), 0.915232, 5e-6),
        ("P(X<=3 | 3.07)", poisson_cdf(3, 3.07), 0.631553, 5e-6),
        ("P(X<=0 | 0.71)", poisson_cdf(0, 0.71), 0.491644, 5e-6),
        ("P(X<=9 | 9.94)", poisson_cdf(9, 9.94), 0.465458, 5e-6),
        ("P(X<=16 | 9.94)", poisson_cdf(16, 9.94), 0.974237, 5e-6),
        ("P(X<=4 | 1.024)", poisson_cdf(4, 1.024), 0.995959, 5e-6),
        ("P(X<=15 | 9.94)", poisson_cdf(15, 9.94), 0.953312, 5e-6),
    ]
    ok = True
    for label, got, want, tol in checks:
        good = abs(got - want) <= tol
        ok = ok and good
        print(f"{'ok  ' if good else 'FAIL'} {label} = {got:.6f} (expected ~{want})")

    # The permutation test must not fire on identical arms and must fire on a
    # clean separation. Both are checked so a broken shuffle cannot pass.
    null = permutation_p_value([0, 1, 0, 2, 1, 0, 1], [0, 1, 1, 0, 2, 1, 0], iterations=2000)
    strong = permutation_p_value([0, 1, 0, 2, 1, 0, 1], [3, 4, 2, 5, 3, 4, 3], iterations=2000)
    for label, got, want_high in (
        ("permutation p on identical arms", null["p_value"], True),
        ("permutation p on separated arms", strong["p_value"], False),
    ):
        good = (got > 0.20) if want_high else (got < 0.05)
        ok = ok and good
        print(f"{'ok  ' if good else 'FAIL'} {label} = {got:.3f}")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--stars", type=int, default=DEFAULT_STARS)
    p.add_argument("--age-days", type=int, default=DEFAULT_AGE_DAYS)
    p.add_argument("--views-per-day", type=float, default=DEFAULT_VIEWS_PER_DAY)
    p.add_argument("--views-sd", type=float, default=DEFAULT_VIEWS_SD)
    p.add_argument("--json", action="store_true")
    p.add_argument("--self-test", action="store_true")
    p.add_argument(
        "--analyze",
        metavar="A,B",
        help=(
            "confirmatory read: comma-separated daily unique-view counts for arm A "
            "and arm B, e.g. --analyze '0,1,0,2,1,0,1:1,3,2,4,2,3,2'"
        ),
    )
    p.add_argument("--iterations", type=int, default=20000)
    args = p.parse_args(argv)

    if args.self_test:
        return self_test()

    if args.analyze:
        try:
            left, right = args.analyze.split(":", 1)
            arm_a = [float(x) for x in left.split(",") if x.strip() != ""]
            arm_b = [float(x) for x in right.split(",") if x.strip() != ""]
        except ValueError:
            print("error: --analyze wants 'a1,a2,...:b1,b2,...'", file=sys.stderr)
            return 2
        result = permutation_p_value(arm_a, arm_b, iterations=args.iterations)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(render_analysis(result))
        return 0

    if args.age_days <= 0 or args.views_per_day <= 0:
        print("error: --age-days and --views-per-day must be positive", file=sys.stderr)
        return 2

    report = build_table(args.stars, args.age_days, args.views_per_day, args.views_sd)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
