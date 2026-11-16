# GH-EXP-001 — "Prove It" hero: a pre-registered growth experiment

**Owner:** Growth Hacker · **Seat:** Growth / Experimentation
**Repo:** https://github.com/bythewayz66-glitch/mem20 · **Branch read:** `main`
**Baseline HEAD:** `0224a64946a2c00313a9872515893157adcbc47e` (2026-11-16 06:55:07 +0000)
**Release under test:** `VERSION` = **4.0.0** · live page serves **v4.0.0** (verified this run)
**Written:** 2026-11-16 · **Status:** pre-registered, **not yet runnable** — see §7
**Companion:** `scripts/gtm/experiment_power.py` (all arithmetic in this brief is that script's output)

> **What this document is.** A growth experiment designed to be *falsifiable before it is run*.
> The hypothesis, the metric, the sample size, the analysis and the guardrails are all fixed here,
> in git, before any traffic is touched. The sample size is not a round number someone liked — it is
> the output of an exact test against the repo's own measured baseline, and the script that produces
> it is committed alongside so anyone can re-run it and get the same table.
>
> **What this document is not.** It is not a launch plan, and it does not claim the experiment can
> start today. §7 states the precondition that is currently unmet, with the measurement that shows it.

---

## 1. Why this experiment, and why now

The 4.0.0 release is shipped and the public page serves it. The growth problem is not the product —
it is that **the page does not make the product's one defensible claim in the first screen.**

The wedge is fixed and is not up for debate: *auditable agent memory — grounded vs simulated,
enforced at the storage layer.* The repo demonstrates it in code. The page, as served, leads with
something else. A visitor who arrives from a directory listing or a README link has to scroll to
learn what makes mem20 different from every other memory layer, and most do not.

So the experiment is narrow on purpose: **does leading with the auditable-partition claim, in the
hero, move the only metric that is both meaningful and measurable today?**

### 1.1 The metric choice is forced by the measurement stack, not by preference

`docs/gtm/launch-instrumentation.md` establishes, with evidence, that the public page carries **no
analytics snippet** and that GitHub's `traffic/referrers` and `traffic/paths` endpoints both return
**404** for this repo. The consequences are binding on any experiment design:

| Candidate primary metric | Available? | Why |
|---|---|---|
| Per-channel sessions | **No** | Needs a snippet reading `utm_*`; none present |
| On-page events (CTA click, install copy) | **No** | No event stream exists |
| Activation (first useful memory op) | **No** | No telemetry at that boundary |
| **Unique repo views / day** | **Yes** | `traffic/views`, 14-day rolling window |
| Stars / forks | **Yes** | Point-in-time counters, delta over a window |
| Clones | Yes, but **contaminated** | 901 unique cloners vs 8 unique viewers is automation, not interest |

**Primary metric: unique repository views per day** (`traffic/views`, `uniques`).
It is the only top-of-funnel signal that is real, attributable to a *time window* rather than a
channel, and not dominated by CI. Stars are the secondary metric and are reported, but they are too
sparse to carry a 14-day read (§4.2 shows why, numerically).

---

## 2. Hypothesis

> **H1.** Replacing the current hero on the public page with the "prove it" hero — which leads with
> the grounded/simulated partition and the auditability claim, and moves the install command above
> the fold — increases **unique repository views per day** by at least **1.55x** over the
> pre-registered window, relative to the current hero.

Stated as a null and an alternative, because that is what gets tested:

- **H0:** the treatment hero produces the same daily unique-view rate as the control hero.
- **H1 (one-sided):** the treatment hero produces a higher daily unique-view rate.

**Direction is pre-registered as one-sided.** A hero rewrite that *reduces* repo views is a real
outcome and will be reported as such, but it is not the alternative this test is powered against;
spending half the alpha on a direction nobody is trying to achieve would only make the test weaker.

### 2.1 What would make this hypothesis false

Written down now so it cannot be reinterpreted later:

1. The treatment arm's daily unique views are not higher than the control arm's at p ≤ 0.05.
2. The lift is real but the guardrails in §6 are breached (e.g. the page's own load or the repo's
   issue queue degrades), in which case the result is void regardless of the metric.
3. The lift appears only in the first 48 hours and decays to baseline — a novelty spike, not an
   effect. §5.3 pre-commits to reporting the first-48h and steady-state windows separately for
   exactly this reason.

---

## 3. Design

### 3.1 Arms

| Arm | Hero | Everything else |
|---|---|---|
| **A — control** | The hero as currently served on `mem20.com` | unchanged |
| **B — treatment** | "Prove it" hero: partition claim first, install command above the fold, benchmark caveat visible | unchanged |

Only the hero block differs. Nav, footer, links and the rest of the page are byte-identical between
arms, so the comparison isolates the hero and nothing else.

### 3.2 Randomisation: a day-level switchback

The page is static and carries no snippet, so **per-visitor randomisation is not available** — there
is no client-side code to assign a visitor to an arm, and no way to record which arm they saw. The
only randomisation this stack can actually execute is a **day-level switchback**:

- Each calendar day, the live page serves exactly one arm.
- The arm for each day is assigned by a **pre-committed coin flip**, generated and committed before
  the experiment starts, so the assignment cannot be influenced by how the first days look.
- The unit of randomisation is therefore the **day**, and the effective sample size is the number of
  days, not the number of visitors.

This is a real randomised experiment, and it is the honest design for a static page with no
instrumentation. Its cost is stated plainly in §4.3: day-level randomisation is far less efficient
than visitor-level, and the power table reflects that rather than hiding it.

**Why not a simple before/after?** Because a before/after cannot separate the hero from anything
else that changes over the same window — a directory listing going live, a post landing, a CI
change. The switchback randomises those away across arms.

### 3.3 Window

| Parameter | Value | Rationale |
|---|---|---|
| Primary window | **14 days** | Matches the GitHub traffic API's rolling window; the longest read the data source supports without losing the start of the experiment |
| Days per arm at 14 days | 7 | 14 / 2 |
| Minimum days per arm | **7** | Below this the normal approximation on arm means is not defensible |
| Extension | **to 56 days** | Pre-committed: if the 14-day read is inconclusive, the experiment continues to 56 days rather than being re-run. §4.3 shows 56 days is where a 2x effect becomes detectable |

**The extension is pre-registered, not optional.** Stopping at 14 days and then re-running a fresh
14-day experiment would be a second look at the same question, and the alpha would no longer mean
what it says. One experiment, one pre-committed extension, one final read.

---

## 4. Sample size

All figures below are the output of `scripts/gtm/experiment_power.py` at the baseline HEAD. The
script is dependency-free and self-testing; §8 gives the exact commands to reproduce every number.

### 4.1 Measured baseline

| Quantity | Value | Source |
|---|---|---|
| Stars | **3** | GitHub API `repos/bythewayz66-glitch/mem20` → `stargazers_count`, this run |
| Repo age | **41 days** | `created_at` 2026-10-06 → measured 2026-11-16 |
| Star rate | **0.07 / day** | 3 / 41 |
| Unique repo views | **0.71 / day** (sd **0.83**) | `traffic/views`, 14-day window ending 2026-10-31 |
| Variance / mean of daily views | **0.97** | (0.83²) / 0.71 |

**The variance-to-mean ratio of 0.97 is the reason this brief uses a Poisson model.** A ratio near 1
is the signature of a Poisson process, and it is *measured here*, not assumed. The script also
computes the Poisson-implied coefficient of variation (1.19) and compares it to the measured one
(1.17) — they agree to within 2%, which is the evidence that the model is appropriate rather than
convenient.

### 4.2 Single-arm read — exact Poisson test

The primary read is a count of discrete events in a fixed window, so the test is an **exact
one-sided Poisson test**, not a t-test. At a baseline of 0.71 views/day, a 14-day window expects
**9.94** events; the test rejects the null when the observed count reaches **16** —
P(X ≥ 16 | 9.94) = 0.047, source: `scripts/gtm/experiment_power.py`.

```
metric                      MDE   k*     lam0     lam1  power@14d  days needed
------------------------------------------------------------------------------
unique_repo_views_per_day    2x   16     9.94    19.88       0.84           13
unique_repo_views_per_day    3x   16     9.94    29.82       1.00            5
unique_repo_views_per_day    5x   16     9.94    49.70       1.00            2
stars_per_day                2x    4     1.02     2.05       0.15          124
stars_per_day                3x    4     1.02     3.07       0.37           42
stars_per_day                5x    4     1.02     5.12       0.75           16
```

Read the two blocks separately, because they say different things:

- **Views are workable.** A 2x lift is detected with power 0.84 in a 14-day window; a 3x lift in 5
  days. The primary metric can carry the experiment.
- **Stars are not.** A 2x lift in the star rate needs **124 days** to reach 80% power, and even a 5x
  lift needs 16. **This is why stars are secondary and not primary.** A 14-day star read would be
  noise dressed as a result, and the table is here so nobody proposes one.

### 4.3 Two-arm switchback — the design actually being run

The single-arm table above answers "is the count higher than baseline?" The switchback answers the
question the experiment actually asks — "is arm B higher than arm A?" — and it is less sensitive,
because the day is the randomisation unit and the between-day variance is large relative to the
mean.

```
day-level switchback (two-arm, normal approximation on daily counts)
  window  days/arm   SE(diff)   MDE abs   MDE rel  detects 2x
-------------------------------------------------------------
      14         7       0.44      1.10      1.55         yes
      28        14       0.31      0.78      1.10         yes
      56        28       0.22      0.55      0.78         yes
```

**The pre-registered sample size is 14 days (7 days per arm), and the smallest lift it can detect is
1.55x.** That is the number the hypothesis in §2 is written against — not 2x, because 2x is not what
a 14-day switchback is powered for. The 56-day extension detects 0.78x, which is why it is the
pre-committed fallback rather than a fresh experiment.

### 4.4 The traffic precondition — the finding that matters most

The switchback's sensitivity depends on the coefficient of variation of the daily counts, not on
their level. Raising traffic is therefore exactly what buys sensitivity. Inverting the relation
answers the question that has to be answered *before* committing 14 or 56 days:

```
traffic precondition - mean unique views/day needed to detect a lift
  window  target lift  views/day (meas)  views/day (Pois)  x baseline
---------------------------------------------------------------------
      14        2.00x              0.60              0.62         0.9
      14        3.00x              0.27              0.28         0.4
      28        2.00x              0.30              0.31         0.4
      28        3.00x              0.13              0.14         0.2
      56        2.00x              0.15              0.16         0.2
      56        3.00x              0.07              0.07         0.1
```

**The measured baseline of 0.71 unique views/day already clears every requirement in this table.**
The binding constraint is not traffic volume — it is the *number of days*, and the day-level
randomisation that forces it. This is the opposite of the usual growth-experiment problem, and it is
worth stating because it changes what the team should do next: the lever is not "get more traffic",
it is "get a per-visitor randomisation mechanism", which is the same snippet that §7 asks for.

### 4.5 Attribution sensitivity — the caveat that bounds the whole design

The primary metric is unique **repo** views. The page is only one of several ways a person reaches
the repo — README links, directory listings, direct links, search. If the page accounts for a share
`s` of repo views, a page-level multiplier `m` shows up on the total as `m·s + (1 − s)`. Inverting:

```
attribution sensitivity - page-level lift needed for the total read
  page share of repo views  total lift  page lift needed
--------------------------------------------------------
                      100%       1.55x             1.55x
                       50%       1.55x             2.10x
                       25%       1.55x             3.20x
                       10%       1.55x             6.50x
```

**The page share is not measurable today** — `traffic/referrers` is 404, so there is no way to know
what fraction of repo views the page drives. At a 10% share, a 1.55x total read would require a
**6.50x page-level effect**, which no hero rewrite produces.

**This is the single most important limitation of the design, and it is why the experiment is
described as a screen rather than a verdict.** A positive result is strong evidence the hero works.
A null result is *not* evidence the hero fails — it may simply mean the page's share of repo views
is too small for the effect to surface in the total. §5.4 pre-commits to reporting it that way.

---

## 5. Analysis plan

### 5.1 Confirmatory test

**One-sided permutation test on the difference of arm means**, 20,000 permutations, fixed seed
`20261116`. The day label is the randomisation, so permuting labels is the correct null: it asks how
often a difference this large arises when the arm assignment carried no information. No
distributional assumption is required, which matters because the daily counts are small.

Reject H0 at **α = 0.05**, one-sided. The test is implemented in the companion script and is
exercised in both directions by its self-test (it must not fire on identical arms, and must fire on
a clean separation).

### 5.2 Secondary metrics — reported, not tested

Stars, forks and clones are reported as deltas with their windows. **Clones are labelled
automation-contaminated** in every report, per `launch-instrumentation.md` §3. No secondary metric
is used to declare the experiment a win.

### 5.3 Pre-committed windows

Reported separately, always, in this order:

1. **First 48 hours** — novelty window. A spike here that decays is a novelty effect, not an effect.
2. **Steady state (day 3 → end)** — the window the hypothesis is actually about.
3. **Full window** — for completeness, never on its own.

### 5.4 Pre-committed interpretation

| Outcome | What is reported |
|---|---|
| p ≤ 0.05, guardrails clean | Hero effect supported at the pre-registered MDE. State the MDE; do not claim a point estimate as the effect size. |
| p > 0.05 | **Inconclusive, not negative.** State the page-share limitation (§4.5) in the same sentence as the result. |
| Any guardrail breached | **Void.** Report the breach and the metric together; do not report the metric alone. |
| Lift only in the first 48h | **Novelty, not effect.** Report as such. |

### 5.5 What will not be done

- No peeking and stopping early on a favourable day. The window is fixed; the extension is fixed.
- No re-running the 14-day experiment after an inconclusive read. The extension is the second look.
- No per-channel claims. There is no attribution, so there are no per-channel numbers to report.
- No averaging the arms' modes, no composite "engagement score", no metric invented after the fact.

---

## 6. Guardrails

Guardrails are checked **daily** during the window. Any breach voids the run (§5.4).

| # | Guardrail | Threshold | Why it is here |
|---|---|---|---|
| G1 | Page availability | `mem20.com` returns 200 on every daily check | A hero that breaks the page is not a win |
| G2 | Page payload size | Treatment hero ≤ **1.25x** control hero bytes | Guards against a hero that bloats the page |
| G3 | Repo issue queue | No more than **+3** net new issues attributable to the hero's claims | A claim that generates confusion is a cost, not a win |
| G4 | Claim integrity | Every claim in the treatment hero is in `docs/gtm/claim-ledger.md` | The wedge is auditability; a hero that overclaims destroys it |
| G5 | Benchmark caveat | The adversarial row stays visible wherever a retrieval figure appears | Binding rule from the claim ledger; not waivable for a test |
| G6 | Install path | Source-only; no PyPI implication anywhere in the hero | The packages 404 on PyPI |
| G7 | No `/sites/` destination | The hero links only to anonymous-reachable URLs | `/sites/` returns 403 to every anonymous visitor |

**G4–G7 are not experiment-specific.** They are the standing content rules from the claim ledger and
the launch gate, and the experiment does not get to suspend them. `scripts/check_gtm_claims.py`
mechanically enforces the machine-checkable subset.

---

## 7. Precondition — why this cannot start today

**The experiment is pre-registered and not runnable.** The blocker is not the design; it is the
measurement stack, and it is the same blocker the launch gate already names.

`scripts/check_launch_gate.py`, run against the live site this session:

```
  [PASS] anonymous       https://mem20.com/ returned 200, 10998 bytes, no access token
  [PASS] version         served page carries 4.0.0 x1; no retired version strings
  [FAIL] social_preview  no og:image on the served page -> HN/PH/Reddit/X render a bare grey box
  [FAIL] https_hop       canonical link hops through plaintext: 301 -> http://mem20.com/
  [FAIL] crawlable       robots.txt returned 404 (want 200)
  [FAIL] analytics       no analytics snippet on the served page -> every utm_* link is decorative
  [FAIL] repo_homepage   repo homepage ... returned 403 - this is a /sites/ artifact

LAUNCH GATE: BLOCKED - 5 of 7 gates failed, 2 passed.
```

Two of these bear directly on this experiment:

1. **`analytics` — no snippet.** This is what forces the day-level switchback instead of
   per-visitor randomisation, and it is what makes §4.5's page-share caveat unmeasurable. Adding a
   privacy-respecting snippet (Plausible, Umami, or a self-hosted counter) converts this experiment
   from a 14-day screen into a per-visitor test with roughly an order of magnitude more sensitivity.
2. **`repo_homepage` — the repo's homepage field is a `/sites/` URL returning 403.** The
   most-clicked link on the repo is a dead end. Fixing it is one field, and it directly affects the
   primary metric, because a dead-end homepage suppresses exactly the repo views this experiment
   measures.

**The precondition for starting GH-EXP-001 is therefore:** the hero arms are built and the page
serves them, and the repo `homepage` field resolves 200. The analytics snippet is not strictly
required to run the switchback — the design works without it — but it is required to make the result
attributable, and it is the highest-leverage change available.

**This document does not fix any of those.** It is the experiment, pre-registered, so that when the
precondition clears the test can start without a design debate.

---

## 8. Reproduction

Every number in this brief comes from the committed script. From a checkout of `main`:

```bash
# the full pre-registered table (this brief's §4)
python3 scripts/gtm/experiment_power.py

# machine-readable form
python3 scripts/gtm/experiment_power.py --json

# verify the statistics before trusting the table
python3 scripts/gtm/experiment_power.py --self-test

# recompute against a different baseline
python3 scripts/gtm/experiment_power.py --stars 3 --age-days 41 --views-per-day 0.71

# the confirmatory read, once the window has run
python3 scripts/gtm/experiment_power.py --analyze '0,1,0,2,1,0,1:3,4,2,5,3,4,3'
```

`--self-test` checks the Poisson CDF against seven independently computed reference values and
checks the permutation test in both directions. It exits non-zero on any failure, so it is usable as
a CI step.

**Baseline provenance.** The view and star figures are point-in-time measurements, not constants.
`traffic/views` is a 14-day rolling window, so the baseline decays out of the API as time passes;
re-run the script with fresh `--views-per-day` and `--stars` values before starting the experiment,
and record the new baseline in the run log. The design does not change when the baseline does — only
the numbers in §4 do.

---

## 9. Hand-off

| Item | State |
|---|---|
| Hypothesis, metric, sample size, guardrails | **Pre-registered in this file** |
| Sample-size arithmetic | **Committed and self-testing** — `scripts/gtm/experiment_power.py` |
| Hero arms (control / treatment) | **Not built** — needs the Webpage Developer seat |
| Analytics snippet | **Not present** — owner decision, `launch-instrumentation.md` §6 |
| Repo `homepage` field | **403** — repo admin, one field |
| Experiment run | **Not started** — blocked on §7 |

**The one decision this brief asks for** is the same one `launch-instrumentation.md` §6 already
asks: add a privacy-respecting analytics script to the public page, or accept that the launch — and
this experiment — runs without attribution. The experiment is designed to work either way; it is
simply much stronger with it.
