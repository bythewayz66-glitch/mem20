# mem20 4.0 — Subsystem Renovation Plan

**Issued:** 2026-11-01 · **Owner directive:** bythewayz66 · **Prepared by:** Mem20-admin (work-preservation & ops watchdog)
**Baseline commit:** `48c241a1edff1fdc9f0d0b38f51796c3c8b88b2b` (main, tag `v3.1.2`, 2026-11-01T17:33:30Z)
**Repo of record:** `github.com/bythewayz66-glitch/mem20` (public). `JaysonAIOnline/mem20` returns 404 — not the live repo.
**Target release:** mem20 **4.0**

> **Standing rule (owner, restated):** a deliverable exists only as a **40-char commit SHA on a pushed branch** or a **permanent URL committed under `docs/`**. Chat-only claims do not count and are scored as absent.

---

## 1. What this plan is

The owner directive of 2026-11-01 supersedes the wave-2 roster. Every mem20 subsystem must become a
first-class, production-ready submodule meeting **seven** acceptance criteria. This document is the
committed renovation plan: measured inventory, per-subsystem owner, branch name, acceptance criteria,
and sequencing.

The inventory below is **measured, not estimated** — produced by walking the tree at the baseline
commit and by running the conformance gate (`scripts/renovation/conformance.py`) against every
subsystem. Every number in this document is reproducible with the commands in §7.

---

## 2. Measured baseline — the honest starting point

| Metric | Value |
|---|---|
| Subsystems discovered (≥5 Python files) | **209** |
| Plus non-Python subsystems named in the directive (`braid` Rust, `gateway`) | **+2 → 211 total** |
| Total Python source LOC across subsystems | **205,153** |
| Rust LOC in `braid/` (63 `.rs` files) | 12,621 |
| Subsystems fully conformant (7/7) | **0** |
| Subsystems at 6/7 | 2 |
| Subsystems at 5/7 | 42 |
| Subsystems at 4/7 | 148 |
| Subsystems at 3/7 | 17 |
| Stub markers found (TODO / FIXME / NotImplementedError) | **56 across 9 subsystems** |

### 2.1 Per-criterion pass rate — where the real gap is

| # | Criterion | Passing | Rate |
|---|---|---|---|
| 1 | Domain logic present | 209 / 209 | 100% |
| 2 | No stubs | 200 / 209 | 95.7% |
| 3 | Tests present | 200 / 209 | 95.7% |
| 4 | CLI surface | 192 / 209 | 91.9% |
| 5 | README with runnable example | 59 / 209 | **28.2%** |
| 6 | **≥5 other mem20 modules imported and used** | **0 / 209** | **0.0%** |
| 7 | Registered with MCP server / gateway | 5 / 209 | **2.4%** |

**Read this plainly.** The repo is not short of code — 205k LOC already exists and domain logic is
universally present. The renovation is not a rewrite; it is a **wiring and hardening** job. Two
criteria are effectively at zero across the entire program:

- **Criterion 6 (≥5-module dependency wiring) is 0/209.** No subsystem currently imports five other
  mem20 modules. The highest observed is `mcp` at 4. This is the single largest piece of work in the
  program and the one that turns 209 silos into one ecosystem.
- **Criterion 7 (MCP/gateway registration) is 5/209.** Only `mcp`, `mem20_mcp`, `gateway`,
  `memory_engine` and `toolchest` are reachable from the server surface. 204 subsystems are
  unreachable by any client.

Criterion 5 (README examples) at 28% is the cheapest win and should be batched with criterion 6,
since writing the example is how you prove the wiring works.

### 2.2 Stub debt — 56 markers, 9 subsystems

These are the only subsystems that fail criterion 2. They are named here so no agent has to hunt:

| Subsystem | Stub markers |
|---|---|
| `mem20gamez` | 5 |
| `mem20yetiz` | 4 |
| `mem20orcaz` | 3 |
| `mem20unitiz` | 3 |
| `mem20rpgz` | 2 |
| `mem20sitemapz` | 1 |
| `mem20factoryz` | 1 |
| `mem20langz` | 1 |
| `mcp` | 1 |

---

## 3. Acceptance criteria — machine-checkable, not prose

A subsystem is **DONE** only when `scripts/renovation/conformance.py <subsystem>` exits 0. The gate
enforces all seven criteria:

| # | Criterion | Gate check |
|---|---|---|
| 1 | Domain logic, 100% real | ≥1 non-test source file, ≥50 source LOC |
| 2 | No stubs | zero matches for `TODO`/`FIXME`/`XXX`/`NotImplementedError`/`raise NotImplemented`/`pass # stub` |
| 3 | Tests (unit + integration) | ≥1 test file, and `pytest` green on the subsystem |
| 4 | CLI surface | `cli.py`, `__main__.py`, `main.py`, or a `cli/` package |
| 5 | README with runnable example | `README.md` containing ≥1 fenced code block |
| 6 | ≥5 other mem20 modules imported **and used** | AST scan: ≥5 distinct top-level `mem20*` / core modules imported |
| 7 | Registered with MCP server / gateway | subsystem name present in an MCP/gateway registry file |

**Additional evidence required per subsystem, beyond the gate:**

- A **40-character commit SHA** on a pushed branch (not a short SHA, not a chat paste).
- `pytest` output pasted into the task card showing the test count and pass status.
- The README example must be **executed** in the agent's run, with its real output pasted — an
  example that was never run does not satisfy criterion 5.
- Criterion 6 is satisfied by **real use**, not a bare import: the imported module's function must be
  called on a code path the tests exercise. The gate checks imports; the reviewer checks use.

---

## 4. Sequencing — three waves

Waves are ordered by **risk and dependency**, not by size. Wave 1 establishes the shared substrate
that every later subsystem wires into; without it, criterion 6 work in waves 2–3 would be built
against a moving target.

| Wave | Subsystems | LOC in scope | Agents |
|---|---|---|---|
| **1 — Substrate** | **23** | 86,929 | 12 |
| **2 — Core product surface** | **137** | 95,569 | 16 |
| **3 — Long tail** | **51** | 34,674 | 8 |

### Wave 1 — Substrate (23 subsystems, 12 agents)

**Why first:** these are the modules every other subsystem must import to satisfy criterion 6. If
they change shape mid-program, every downstream branch rebases. They also carry the MCP/gateway
registration surface (criterion 7), so landing them first makes criterion 7 a one-line change for
everyone else.

The 23 wave-1 modules, exactly:

```
braid  gateway  mcp  mem20_mcp  memory_engine  toolchest
mem20agentz  mem20corez  mem20crewz  mem20dreamz  mem20kilnz  mem20meshz
mem20ops  mem20orcaz  mem20verify  mem20wasmz
mem20apishapeshiftinggatewayz  mem20crossruntimeeventlatticez
mem20eventstreamsuperhighwayz  mem20reversibleexecutiongraphz
mem20selfhealingruntimecivilizationz  mem20universalhealthnervoussystemz
mem20versioncontrollargeassetandrecoverypipelinez
```

| Owner | Wave-1 modules |
|---|---|
| Server Builder | `mcp`, `mem20_mcp`, `gateway`, `mem20meshz`, `mem20apishapeshiftinggatewayz` |
| AI Engineer | `mem20agentz`, `memory_engine`, `mem20dreamz`, `mem20crewz`, `mem20kilnz` |
| Super Agent | `toolchest`, `mem20corez`, `mem20verify`, `mem20ops` |
| mem20 Orchestrator | `mem20orcaz` |
| GitHub Repo Assistant | `mem20versioncontrollargeassetandrecoverypipelinez`, `mem20reversibleexecutiongraphz` |
| mem20-sybsystems | `mem20selfhealingruntimecivilizationz`, `mem20universalhealthnervoussystemz` |
| Mem20 C++ Expert | `braid` (Rust), `mem20wasmz` |
| Analytics Reporter | `mem20eventstreamsuperhighwayz`, `mem20crossruntimeeventlatticez` |

**Wave 1 exit gate:** `mcp`, `memory_engine`, `toolchest`, `gateway`, `mem20corez` all at 7/7, and a
published `docs/renovation/4.0/SUBSTRATE.md` naming the stable public API of each — the contract
waves 2–3 import against.

### Wave 2 — Core product surface (137 subsystems, 16 agents)

Every remaining subsystem owned by a wave-1 or wave-2 agent. Focus areas:

| Owner | Focus |
|---|---|
| Webpage Developer | `mem20owebz`, `mem20studioz`, `mem20visualdataflowcomposerz`, `mem20instantappsynthesisz` |
| mem20-webdev | `mem20sitemapz`, `mem20officez`, `mem20shopz`, `mem20kanbanz`, `mem20teamz` |
| mem20-frontends | `mem20controlz`, `mem20facez`, `mem20realtimeteampresencez`, `mem20ambient*` |
| Mem20-Perl-Expert | `mem20langz`, `mem20modalitybridgez`, `mem20intentcompilerz`, `mem20intenttomissioncompilerz` |
| Mem20-Ruby-Expert | `mem20agentz_sdk`, SDK packaging |
| Mem20 Benchmark Dataset Builder | `mem20benchmarkz`, `mem20syntheticevaluatorarenaz`, `mem20executabledesignstresslabz` |
| Experiment Tracker | `mem20twinz`, `mem20executiondigitaltwinz`, `mem20outcomesimulationlabz` |
| mem20 GTM Team Lead | `mem20offergenomeenginez`, `mem20offerassemblyfabricz`, `mem20customerlifecycleenginez` |

### Wave 3 — Long tail (51 subsystems, 8 agents)

| Owner | Focus |
|---|---|
| Market Research | `mem20opportunityradarz`, `mem20federatedresearchgridz`, `mem20acquisitionandpartnershipscoutz` |
| Pricing Analyst | `mem20uniteconomicsautopilotz`, `mem20servicebundlingenginez`, `mem20resourceexchangemarketz` |
| Finance Assistant | `mem20revenueleakhunterz`, `mem20businessmodelsimulatorz` |
| Growth Hacker | `mem20productledgrowthsimulatorz`, `mem20crossproductloyaltygraphz`, `mem20communitychallengeenginez` |
| Mem20 Content Creator | `mem20dynamicnarrativeenginez`, `mem20narrativedialogueandlocalizationpipelinez`, `mem20styleguideagentz` |
| Slides Assistant | `mem20audiovoiceandmusicpipelinez`, `mem202dand3dartproductionoptimizationpipelinez`, `mem20rigginganimationandmotionpipelinez` |
| UX Researcher | `mem20humanagentcoworkcanvasz`, `mem20personalworkflowtwinz`, `mem20playermotivationtwinz` |
| Mem20-naration | `mem20liveprojectdemonstrationenginez`, `mem20ambientteamradioz` |

The **complete, authoritative per-subsystem assignment** — all 211 rows with owner, wave, branch
name, LOC, and current conformance score — is in
[`subsystem-assignments.csv`](./subsystem-assignments.csv). That file is the source of truth; the
tables above are summaries. Regenerate it at any time with `scripts/renovation/build_inventory.py`.

---

## 5. Branch and commit conventions

- **One branch per subsystem:** `feat/4.0-<agent-slug>-<subsystem>`, e.g.
  `feat/4.0-server-builder-mcp`. Exact names are in the CSV.
- **One subsystem per branch.** Do not bundle two subsystems into one branch — it makes the
  conformance gate result ambiguous and blocks independent review.
- **Commit message:** `feat(<subsystem>): 4.0 conformance — <what changed>`.
- **No force-push to `main`.** No direct commits to `main`. Every subsystem lands via PR.
- **Token transport:** every push uses the owner-supplied fine-grained PAT per
  `docs/ops/token-mandate-2026-11-01.md`. Never write the token into a tracked file, workflow YAML,
  committed `.git/config`, commit message, branch name, or PR body. Report it redacted as
  first-12-chars + ellipsis.
- **Collision guards (unchanged from the wave-2 roster):** do not edit `docs/index.html`,
  `docs/dashboard.html`, `published/daily-reports/**`, root `README.md`, or `mcp/**` unless your
  subsystem *is* `mcp`. Root `README.md` and `mcp/**` are owned by Server Builder in wave 1.

---

## 6. Known blockers carried into 4.0

These are live facts as of the baseline commit and will bite agents who assume otherwise:

| Blocker | Status | Impact on 4.0 |
|---|---|---|
| `mem20` not on PyPI (`mem20`, `mem20-ai`, `mem20oreo` all 404) | open | install stays source-only: `git clone` + `pip install -r requirements.txt`. No README may claim `pip install mem20`. |
| Sidney host `216.198.115.91` | ports 2222/9900 errno 113, 22/80 timeout | `gabe` publish path unavailable; all 4.0 evidence must be GitHub SHAs, not Sidney URLs. |
| `mem20.jaysonai.online` | NXDOMAIN on Cloudflare + Google DoH | hostname is being retired; do not wire it into any subsystem. |
| `mem20.org` / `.store` / `.info` | 404 (GitHub Pages allows one custom domain; `docs/CNAME` = `mem20.com`) | only `mem20.com` serves. |
| Tag `v3.0.0` | 93+ commits behind main | superseded by `v3.1.2`; 4.0 will cut its own tag. |
| Benchmark coverage | only 2 of 7 retrieval modes scored; adversarial hit-rate 0.000 | Benchmark Builder owns closing this in wave 2. |

---

## 7. How to reproduce every number in this document

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
git checkout 48c241a1edff1fdc9f0d0b38f51796c3c8b88b2b

# full conformance sweep across all 209 subsystems
python3 scripts/renovation/conformance.py --all --json /tmp/conf.json

# one subsystem, human-readable
python3 scripts/renovation/conformance.py mem20kilnz

# regenerate the inventory + assignment CSV
python3 scripts/renovation/build_inventory.py
```

The gate exits non-zero when a subsystem fails, so it drops straight into CI as the 4.0 release gate:

```bash
python3 scripts/renovation/conformance.py --all --fail-under 1.0
```

---

## 8. Release gate for mem20 4.0

mem20 4.0 ships when **all** of the following hold, each backed by a check run at release time:

1. `conformance.py --all --fail-under 1.0` exits 0 — all 211 subsystems at 7/7.
2. `pytest` green across the repo, with the test count recorded.
3. Every subsystem's branch merged to `main` via PR; zero unmerged 4.0 branches.
4. `VERSION` = `4.0.0`, `CHANGELOG.md` has a 4.0.0 section, tag `v4.0.0` cut at the release commit.
5. `docs/renovation/4.0/SUBSTRATE.md` public APIs still match what subsystems import (no drift).
6. Root `README.md` tool count reconciled to the measured value (house number 257/26 is stale;
   measured 270/27 as of 2026-10-31 — Server Builder owns the reconciliation).

---

## 9. House numbers (carried, for consistency in all 4.0 copy)

- **257 tools across 26 domains** — house number. Measured value is **270 tools / 27 domains**; the
  discrepancy is a known open item owned by Server Builder. Do not silently change one without the
  other.
- **TAM $1.28B / SAM $282M / SOM $1.68M**
- **Blended ACV $14,000**

---

*Prepared by Mem20-admin. Inventory and conformance figures measured at baseline
`48c241a1edff1fdc9f0d0b38f51796c3c8b88b2b` on 2026-11-01. Nothing in this document is an estimate
that was not labelled as one.*
