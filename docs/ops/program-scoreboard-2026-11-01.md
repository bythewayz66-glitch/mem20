# mem20 Program Scoreboard — 2026-11-01

**Built by:** Analytics Reporter (roster row 21, gap G1)
**Baseline:** `main` = `2ea4492209dfaae6afb22ca884132a0d1849bfcf` (2026-11-01T06:20:25-07:00, "docs(bench): land four-mode retrieval benchmark results for 2026-10-31")
**Repo of record:** `github.com/bythewayz66-glitch/mem20` (public)
**Directive:** `docs/ops/owner-directive-2026-11-01.md` @ `06fa1220e964f84aabac78127fc18463dfa6798d`

> **Reproducibility contract.** Every number on this page is emitted by one script:
> `bash scripts/ops/scoreboard_signals.sh 2ea4492209dfaae6afb22ca884132a0d1849bfcf`
> The script prints the exact command behind each block. No figure here is copied from an
> earlier report, and no figure is estimated. Where a directive figure and a live measurement
> disagree, the live measurement is shown and the disagreement is stated (§6).

---

## 1. Scoreboard

| # | Signal | Value | Status | Command |
|---|---|---|---|---|
| S1 | Check-run pass rate on `main` | **13 / 14 = 92.86 %** | 🟡 1 red | `curl -s "$API/commits/$MAIN_SHA/check-runs?per_page=100"` |
| S2 | Non-`main` branches | **14** at measurement (13 merged, 1 unmerged) — drifts as agents push; see §3 | 🟡 13 stale refs | `git ls-remote --heads origin` + `git merge-base --is-ancestor` |
| S3 | Tag distance, `v3.1.1` → `main` | **63 commits behind** (0 ahead) | 🔴 stale | `git rev-list --left-right --count v3.1.1...origin/main` |
| S4 | PyPI publication | **0 / 3 published** (`mem20`, `mem20-mcp`, `mem20-sdk` all 404) | 🔴 absent | `curl -s -o /dev/null -w '%{http_code}' https://pypi.org/pypi/<pkg>/json` |
| S5 | Open PRs / open issues | **0 / 0** | 🟢 clear | `curl -s "$API/pulls?state=open"` · `curl -s "$API"` |
| S6 | `VERSION` on `main` | **3.1.0** | 🟢 | `git show $MAIN_SHA:VERSION` |
| S7 | Tracked files on `main` | **8,536** | — | `git ls-tree -r --name-only $MAIN_SHA \| wc -l` |
| S8 | Commits on `main` | **470** | — | `git rev-list --count $MAIN_SHA` |
| S9 | Tags total / `archive-*` | **84 / 79** | — | `git ls-remote --tags origin \| grep -v '\^{}'` |

**Composite read:** 4 of 9 signals green, 2 amber, 2 red, 1 informational. The program is
**not** release-clean: the single red check is on `main` itself, the newest tag is 63 commits
stale, and nothing is installable from PyPI.

---

## 2. S1 — Check-run pass rate on `main`

```
total_check_runs    : 14
success             : 13
failure             : 1
other               : 0
pass_rate           : 13/14 = 92.86%
```

The one failure:

| Field | Value |
|---|---|
| Name | `Tests` |
| Check-run id | `124860549243` |
| Conclusion | `failure` |
| Started / completed | 2026-11-01T13:20:39Z → 2026-11-01T13:21:00Z (21 s) |
| Job URL | https://github.com/bythewayz66-glitch/mem20/actions/runs/41310800014/job/124860549243 |
| Annotation | `.github` line 32 — `Process completed with exit code 4.` |

The 13 passing runs: `deploy` ×2, `report-build-status`, `build` ×2, `mem20agentz OREO integration`,
`Gitlink guard`, `Syntax gate`, `controlz desktop wiring`, `Rust braid (issue`, `hygiene`,
`Dependency audit (issue`, `suite`.

**Scope note.** This is the pass rate of the check-runs attached to the `main` commit
`2ea44922` — not a historical pass rate across runs, and not a test-case pass rate. The
`Tests` job's own internal test counts are not exposed by the check-runs API and are therefore
**not** reported here. The directive attributes the exit code to the *Compute diff against the
base* step (`.github/workflows/ci.yml` line 22); the annotation confirms exit code 4 at
`.github` line 32 but does not itself name the step, so the step attribution is the directive's,
not this scoreboard's.

**The failure is inherited, not introduced by this branch.** The same `Tests` job also fails on
this scoreboard's own head `20410a62` (check-run `124922684010`) with the identical annotation —
`.github` line 32, `Process completed with exit code 4.` — while the other 8 completed checks pass
(`Syntax gate`, `Gitlink guard`, `hygiene`, `suite`, `Rust braid`, `Dependency audit`,
`controlz desktop wiring`, `mem20agentz OREO integration`; `CodeRabbit` skipped). This branch's
diff is 2 files, +316/−0, touching neither `.github/` nor any test:

```
git diff --stat 2ea44922..20410a62
 docs/ops/program-scoreboard-2026-11-01.md | 191 +++++
 scripts/ops/scoreboard_signals.sh         | 125 +++++
 2 files changed, 316 insertions(+)
```

So the red check is G1 itself, owned by GitHub Repo Assistant — not a regression from this work.

---

## 3. S2 — Branch count and merge status

```
remote_heads_total  : 15
non_main_heads      : 14
merged_non_main     : 13
unmerged_non_main   : 1
```

> **Live-drift note (read this before re-running).** The numbers above were taken at
> `2ea44922` **before** this scoreboard's own branch was pushed. Branch count is the one signal
> that moves while the program is running: 22 agents are pushing branches concurrently, so a
> re-run minutes later legitimately reports a different total. Observed during this run:
> `14` at measurement → `15` once this branch landed → `24` (14 merged / 10 unmerged) a few
> minutes later as other agents pushed. **The branch total is therefore a point-in-time reading,
> not a stable metric.** The stable, branch-independent figures are:
>
> - **13 merged stale refs** at baseline `2ea44922` — the deletion target, unchanged
> - **1 pre-existing unmerged branch** at baseline (the directive branch)
> - **0 unmerged commits on any of those 13** (`ahead=0` for every one)
>
> Re-run the script for the current total; do not quote the total from this page as if it were
> still current. The other signals (S1, S3, S4, S6–S9) are pinned to `2ea44922` and do not drift.

| State | Ahead | Branch | Head SHA |
|---|---|---|---|
| MERGED | 0 | `bench/ws1-retrieval-modes-2026-10-31` | `35500f4c2e4f7823d8bce840c0f1fe64a8abac39` |
| MERGED | 0 | `chore/cpp-sdk-surface-guard` | `65613e6aaa2cda7a8ef27563f086b9df59a8e23c` |
| MERGED | 0 | `chore/finance-claims-check` | `ed6a5824a245bdd0356af8e3007e9b737e0d8cc9` |
| MERGED | 0 | `chore/launch-copy-accuracy` | `6dd6f9d334b788ffef7ecd7da4feded52a32dc29` |
| MERGED | 0 | `chore/market-claims-consistency` | `773e83e6673714f9deef3d2191403184f70853a4` |
| MERGED | 0 | `chore/narrative-assets-accuracy` | `c0d005cd08d14a5d55c52a7bdb824ff0571c9961` |
| MERGED | 0 | `chore/perl-sdk-surface-guard` | `166053c7c285c3509c949113ecf459c6661ee9eb` |
| MERGED | 0 | `chore/pricing-surface-accuracy` | `5dcaba1afe6161326047282e58688ee9934dcabc` |
| MERGED | 0 | `chore/ruby-sdk-surface-guard` | `c56ccb092eef6858edddd284dddd57828e89ed2f` |
| MERGED | 0 | `chore/ux-docs-accuracy` | `471265744752abefea7b70e71209aff4249c1ffe` |
| MERGED | 0 | `chore/ws1-rebuild-app-bundle-purge-jaysonai` | `68bcf8b4cfd6e640ac74e2f2e5b5888c963fc18d` |
| MERGED | 0 | `docs/ws1-daily-reports-2026-10-31` | `4f20ecfb848f80e2fe4490050ecfb1e178cea401` |
| MERGED | 0 | `docs/ws1-retire-jaysonai-hostname` | `080fdda1df70920993d272ed43d8848fe7830875` |
| **UNMERGED** | **1** | `docs/ws1-owner-directive-2026-11-01` | `06fa1220e964f84aabac78127fc18463dfa6798d` |

**Reading.** 13 of 14 non-`main` heads are ancestors of `main` (`git merge-base --is-ancestor`
returns true, `ahead=0`) — they carry **zero** unmerged commits and are pure stale refs, safe to
delete. The single unmerged head is the directive branch itself, 1 commit ahead of `main`; it is
the branch this scoreboard is committed on top of, so it is expected to be unmerged at measurement
time. **At-risk commits across all side branches: 1** (excluding this scoreboard's own branch).

---

## 4. S3 — Tag distance

```
v3.1.1   tag_commit=52ffe13d0460  ahead_by=0  behind_by=63
v3.1.0   tag_commit=97add7fdf43c  ahead_by=0  behind_by=62
v3.0.0   tag_commit=a366ff741f48  ahead_by=0  behind_by=159
```

`v3.1.1` (`52ffe13d046078822f21d51b38cb76a226dfe42f`, 2026-10-31) is **63 commits behind** `main`
and **0 ahead** — the tag is a strict ancestor, so no release content is missing from `main`; the
tag simply does not describe current `main`. `VERSION` on `main` reads `3.1.0`, i.e. the working
tree is one patch level behind the newest tag while the tag is 63 commits behind the tree.

---

## 5. S4 — PyPI publication status

| Package | HTTP | Meaning |
|---|---|---|
| `mem20` | **404** | not published |
| `mem20-mcp` | **404** | not published |
| `mem20-sdk` | **404** | not published |

**0 of 3 published.** Install path is source-only. No document may claim `pip install mem20`
until this changes. Closing this needs a PyPI token or trusted-publisher setup — an owner action,
not an agent action (directive §4.3).

---

## 6. Corrections to the directive's figures

The directive's §2 register was measured at a slightly earlier moment. Two figures moved; both
are stated here rather than silently reconciled.

| Directive claim | Live measurement | Explanation |
|---|---|---|
| "13 non-`main` heads; all 13 merged → 0 unmerged" | **14 non-`main` heads; 13 merged, 1 unmerged** (15 / 13 / 2 once this branch lands) | The directive branch `docs/ws1-owner-directive-2026-11-01` @ `06fa1220` was pushed after the register was written. It is 1 commit ahead of `main`. The "13 merged" half of the claim still holds exactly. |
| "`v3.1.1` is 63 commits behind" | **63 behind, 0 ahead** — confirmed | No change. |
| "13 `success` / 1 `failure` of 14" | **13 / 1 of 14** — confirmed | No change. |
| "`mem20` / `mem20-mcp` / `mem20-sdk` all 404" | **all 404** — confirmed | No change. |

**Net effect on the gap register:** G2 is *not* closed. It is 13 stale refs plus 1 legitimately
open branch, not 13 stale refs and nothing else. The deletion target for GitHub Repo Assistant
remains the same 13 SHAs listed in §3.

---

## 7. What this scoreboard does not measure

Stated explicitly so no reader infers a metric that was never computed:

- **No historical trend.** One snapshot at `2ea44922`. No pass-rate time series, no burn-down.
- **No test-case-level pass rate.** The check-runs API exposes job conclusions, not assertion counts.
- **No coverage, latency, or benchmark quality score.** Benchmark quality is G9, owned by
  AI Engineer / Experiment Tracker / Benchmark Dataset Builder — not scored here.
- **No revenue, funnel, or TAM/SAM/SOM figures.** House numbers are carried elsewhere; they are
  not signals this script can verify, so they are absent by design.
- **No anonymous-reachability check.** G10 (`/sites/` 403) is mem20-webdev / Growth Hacker territory.

---

## 8. Reproduce

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git && cd mem20
bash scripts/ops/scoreboard_signals.sh 2ea4492209dfaae6afb22ca884132a0d1849bfcf
```

Requires `git`, `curl`, `python3`. No token: the repo is public and the GitHub API is called
unauthenticated (60 req/h ceiling — the script makes 3 API calls).

The script self-heals from a shallow single-branch clone: it fetches `main`, the pinned SHA,
all remote heads, and tags as needed, so the one-line command above works from a fresh
`--depth 1` clone without extra setup.

---

*Analytics Reporter · 2026-11-01 · baseline `2ea44922` · every figure emitted by
`scripts/ops/scoreboard_signals.sh` in this run.*
