# mem20 — All-Agent Contribution Plan (sequenced)

**Issued:** 2026-11-07 · **Owner:** bythewayz66 (`8203682289589573`) · **Prepared by:** Mem20-admin
**Repo of record:** `github.com/bythewayz66-glitch/mem20` (public). `JaysonAIOnline/mem20` returns 404 — not the live repo.
**Baseline measured this run:** `main` = `e34963f3f1c5801a9fd45a424b168eb30d18c5ba` (2026-11-08T05:24:53Z), 26 agents + 1 human in group `3388661668`.
**Scope:** every agent in the Sidney room contributes one real, landed contribution to mem20, **in sequence, one at a time**.

---

## 0. The rule that governs this whole plan

> **A contribution is a commit on a pushed branch. Nothing else counts.**
>
> Chat-only does not count. A plan does not count. A summary does not count. A branch that exists only
> in your sandbox does not count. The only accepted evidence is a **40-character commit SHA on a pushed
> branch** in `bythewayz66-glitch/mem20`, or a **permanent URL committed under `docs/`**.

### 0.1 NO REPORT-BACK — read this twice

**Do not report back to the channel. Do not post a summary. Do not @ the owner. Do not write a status
message.**

Reporting to chat is half the tokens and none of the value. Each agent in this plan is instructed
explicitly:

> **Do the work. Push it. Let GitHub tell the story.**
>
> Your evidence is the SHA. When you are done, your branch head is the report. If you must record
> something, record it in the file you committed — not in the group.

The only channel traffic this plan permits is the **single hand-off @-mention to the next agent in the
sequence**, which carries the baton and nothing else. No agent posts its own results.

### 0.2 One at a time

Agents go **strictly in the order below**. Agent *N+1* does not start until agent *N*'s branch head is
pushed and its SHA is recorded in the ledger (§5). This is deliberate: 26 agents editing one repo
concurrently is how work gets silently reverted.

---

## 1. DO NOT TOUCH — the in-flight subsystem overhaul

The owner is finishing the **4.0 conformance overhaul** right now with three agents. `main` is being
pushed every 5–8 minutes with `fix(conformance): <subsystem> full depth spec` and
`fix: <subsystem> meaningful <thing>` commits. **Every one of those commits rewrites the same shared
files.** If you touch any of them, you will either conflict or silently revert someone's work.

### 1.1 Frozen paths — no agent in this plan may edit these

| Path | Why it is frozen |
|---|---|
| `gateway/mem20_gateway.py` | rewritten by nearly every conformance commit (subsystem registration) |
| `mcp/server.py` | rewritten by every conformance commit (criterion 7 registration) |
| `mcp/tools/**` | a new `<subsystem>_tools.py` is added per conformance commit |
| `docs/app/**` | `README.md` + a new `<slug>/index.html` per conformance commit |
| `DIARY.md`, `failures.md` | appended by the "meaningful <thing>" commits |
| `docs/renovation/4.0/**` | the overhaul's own plan, substrate contract and assignment CSV |
| `docs/surface.json`, `docs/TOOL-DOMAINS.md` | the live tool/domain pin the sweep re-derives |
| `docs/index.html`, `docs/dashboard.html` | published surface, owned by the sweep |
| `published/**` | immutable delivery archive, integrity-pinned by `published/MANIFEST.tsv` |
| root `README.md`, `VERSION`, `CHANGELOG.md` | release surface, owned by the sweep |
| `scripts/renovation/**` | the conformance gate itself |
| **any `mem20<name>z/**` whose subsystem appears in the last 20 commits on `main`** | that subsystem is being rewritten *right now* |

### 1.2 Frozen branches

Do not push to, rebase, merge, or delete any `feat/4.0-*` branch. They are the overhaul's working set.
Do not open a PR that touches a `feat/4.0-*` head.

### 1.3 Which three agents

The owner states three agents are finishing the overhaul. **Commit authorship is uniform
(`bythewayz66-glitch`, the owner's PAT), so authorship cannot attribute them** — I will not guess a
name and present it as fact. What *is* verifiable is the file set and the branch set, and that is what
the freeze above is built on: it is **path-based, so it holds regardless of who the three are**.

The three are most consistent with the wave-1 substrate owners whose branches remain unmerged —
**Server Builder, AI Engineer, Super Agent** — and those three are therefore sequenced **last**
(steps 24–26), after the overhaul has landed. If the owner's three are different, the freeze still
applies unchanged.

### 1.4 Pre-flight check — mandatory before your first edit

```bash
# 1. is anyone already claiming your files?
grep -rl "<path/you/want/to/edit>" docs/handoff/claims/

# 2. is your subsystem in the live sweep?
git log --oneline -20 origin/main | grep -i "<your-subsystem>"

# 3. is your target path in the freeze list above?
```

If **any** of the three returns a hit: **stop, take your fallback contribution (§4), and do not edit.**
A blocked agent that takes its fallback still contributes. An agent that edits a frozen path destroys
someone else's work.

---

## 2. Sequence overview

Ordered by **collision risk, lowest first**. Gates and records land first because they make every
later step verifiable; the three likely-in-flight agents land last.

| # | Agent | Domain | Contribution | Branch |
|---|---|---|---|---|
| 1 | GitHub Repo Assistant | Repo / CI / version control | Contribution-evidence CI gate — fails any PR without a 40-char SHA or 200 URL | `chore/contrib-evidence-gate-2026-11-07` |
| 2 | Mem20-admin | Ops / work preservation | This plan + the live contribution ledger | `docs/ops-contribution-plan-2026-11-07` |
| 3 | mem20-docuguard | Documentation integrity | Doc-count drift gate — fails on any retired count band | `chore/doc-count-gate-2026-11-07` |
| 4 | Mem20 C++ Expert | C++ / Rust (`braid`) | `braid` criterion-6 wiring test + `ctest` in CI | `feat/4.0-mem20-cpp-expert-braid-wiring` |
| 5 | Mem20-Perl-Expert | Perl / language lane | `mem20langz` to 7/7 conformance | `feat/4.0-mem20-perl-expert-mem20langz` |
| 6 | Mem20-Ruby-Expert | Ruby / SDK | `mem20botz` to 7/7 conformance | `feat/4.0-mem20-ruby-expert-mem20botz` |
| 7 | Webpage Developer | Web surfaces | `mem20owebz` to 7/7 conformance | `feat/4.0-webpage-developer-mem20owebz` |
| 8 | mem20-webdev | Web apps | `mem20kanbanz` to 7/7 conformance | `feat/4.0-mem20-webdev-mem20kanbanz` |
| 9 | mem20-frontends | Frontends / desktop | `mem20controlz` to 7/7 conformance | `feat/4.0-mem20-frontends-mem20controlz` |
| 10 | UX Researcher | UX research | `mem20playermotivationtwinz` to 7/7 | `feat/4.0-ux-researcher-mem20playermotivationtwinz` |
| 11 | Experiment Tracker | Experiment tracking | `mem20remoteexperimentlabz` to 7/7 | `feat/4.0-experiment-tracker-mem20remoteexperimentlabz` |
| 12 | Mem20 Benchmark Dataset Builder | Benchmarks / datasets | Score the 5 unscored retrieval modes; publish the 7-mode table | `bench/ws1-retrieval-modes-2026-11-07` |
| 13 | Analytics Reporter | Analytics | `mem20googlez` to 7/7 conformance | `feat/4.0-analytics-reporter-mem20googlez` |
| 14 | mem20 Orchestrator | Orchestration | `mem20prioritycollisionresolverz` to 7/7 | `feat/4.0-mem20-orchestrator-mem20prioritycollisionresolverz` |
| 15 | mem20-sybsystems | Systems / self-healing | `mem20faultcontainmentcellsz` to 7/7 | `feat/4.0-mem20-sybsystems-mem20faultcontainmentcellsz` |
| 16 | Market Research | Market research | `mem20sensorz` to 7/7 conformance | `feat/4.0-market-research-mem20sensorz` |
| 17 | Pricing Analyst | Pricing | `mem20liez` to 7/7 conformance | `feat/4.0-pricing-analyst-mem20liez` |
| 18 | Finance Assistant | Finance | `mem20revenueleakhunterz` to 7/7 | `feat/4.0-finance-assistant-mem20revenueleakhunterz` |
| 19 | Growth Hacker | Growth | `mem20productledgrowthsimulatorz` to 7/7 | `feat/4.0-growth-hacker-mem20productledgrowthsimulatorz` |
| 20 | Mem20 Content Creator | Content | `mem20ircz` to 7/7 conformance | `feat/4.0-mem20-content-creator-mem20ircz` |
| 21 | Slides Assistant | Slides / media | `mem20yetiz` to 7/7 conformance | `feat/4.0-slides-assistant-mem20yetiz` |
| 22 | Mem20-naration | Narration / demo | `mem20gamez` to 7/7 conformance | `feat/4.0-mem20-naration-mem20gamez` |
| 23 | mem20 GTM Team Lead | GTM | `mem20customerlifecycleenginez` to 7/7 | `feat/4.0-mem20-gtm-team-lead-mem20customerlifecycleenginez` |
| 24 | Server Builder | Runtime / gateway / MCP | `mem20runtimecompatibilityenginez` to 7/7 | `feat/4.0-server-builder-mem20runtimecompatibilityenginez` |
| 25 | AI Engineer | AI / memory engine | `mem20episodicmemorygraphz` to 7/7 | `feat/4.0-ai-engineer-mem20episodicmemorygraphz` |
| 26 | Super Agent | Verification / core | `mem20adversarialqacrewz` to 7/7 | `feat/4.0-super-agent-mem20adversarialqacrewz` |

---

## 3. Per-agent specification

Each block is the complete brief for that agent. **Files listed are the only files that agent may
touch.** Anything outside the list is either frozen (§1) or someone else's layer.

### Step 1 — GitHub Repo Assistant
- **Domain:** repository, CI, version control.
- **Contribution:** land the **contribution-evidence gate** — a CI workflow that fails any PR whose
  body carries neither a 40-character commit SHA nor a `200`-verified URL. This is step 1 because it
  mechanically enforces the rest of this plan.
- **Branch:** `chore/contrib-evidence-gate-2026-11-07`
- **Files:** `.github/workflows/contrib-evidence.yml`, `scripts/ops/verify-contrib-evidence.sh`,
  `docs/ops/contrib-evidence-gate.md`
- **Evidence:** 40-char SHA on the branch + the workflow run URL showing it **red** on a seeded
  no-evidence PR and **green** on a compliant one.

### Step 2 — Mem20-admin
- **Domain:** operations, work preservation, evidence ledger.
- **Contribution:** this plan, plus `docs/ops/contribution-ledger-2026-11-07.md` — the live ledger with
  one row per agent, filled in as each branch lands.
- **Branch:** `docs/ops-contribution-plan-2026-11-07`
- **Files:** `docs/ops/agent-contribution-plan-2026-11-07.md`,
  `docs/ops/contribution-ledger-2026-11-07.md`, `docs/ops/README.md` (index row only)
- **Evidence:** 40-char SHA on the branch.

### Step 3 — mem20-docuguard
- **Domain:** documentation integrity.
- **Contribution:** a **doc-count drift gate** — a script that fails when any live doc carries a retired
  tool/domain band (`257/258/259/260/265/268/270/306` tools, `26/27/38` domains) instead of the live
  pin in `docs/surface.json`. Wire it into CI.
- **Branch:** `chore/doc-count-gate-2026-11-07`
- **Files:** `scripts/ops/check-doc-counts.py`, `docs/hygiene/doc-count-gate.md`,
  `.github/workflows/doc-counts.yml`
- **Evidence:** 40-char SHA + a run that fails on a seeded `270/27` doc and passes on `main`.

### Step 4 — Mem20 C++ Expert
- **Domain:** C++ / Rust, `braid`.
- **Contribution:** give `braid` a real criterion-6 wiring test — a Rust integration test that calls
  into ≥5 sibling mem20 modules on a covered code path — and add `ctest` to CI so it actually runs.
- **Branch:** `feat/4.0-mem20-cpp-expert-braid-wiring`
- **Files:** `braid/tests/**`, `braid/Cargo.toml`, `.github/workflows/braid.yml`,
  `docs/sdk/cpp/README.md`
- **Evidence:** 40-char SHA + `cargo test` / `ctest` output with the test count.

### Step 5 — Mem20-Perl-Expert
- **Domain:** Perl, language lane.
- **Contribution:** bring `mem20langz` to 7/7 — the missing pieces are criterion 5 (a README example
  that is actually executed) and criterion 6 (≥5 real sibling imports on a covered path).
- **Branch:** `feat/4.0-mem20-perl-expert-mem20langz`
- **Files:** `mem20langz/**` only.
- **Evidence:** 40-char SHA + `python3 scripts/renovation/conformance.py mem20langz` exiting 0.

### Step 6 — Mem20-Ruby-Expert
- **Domain:** Ruby, SDK.
- **Contribution:** bring `mem20botz` to 7/7 conformance.
- **Branch:** `feat/4.0-mem20-ruby-expert-mem20botz`
- **Files:** `mem20botz/**` only.
- **Evidence:** 40-char SHA + conformance exit 0 for `mem20botz`.

### Step 7 — Webpage Developer
- **Domain:** web surfaces.
- **Contribution:** bring `mem20owebz` to 7/7 conformance.
- **Branch:** `feat/4.0-webpage-developer-mem20owebz`
- **Files:** `mem20owebz/**` only. **Do not** touch `docs/app/**` — that is frozen.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 8 — mem20-webdev
- **Domain:** web applications.
- **Contribution:** bring `mem20kanbanz` to 7/7 conformance.
- **Branch:** `feat/4.0-mem20-webdev-mem20kanbanz`
- **Files:** `mem20kanbanz/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 9 — mem20-frontends
- **Domain:** frontends, desktop shell.
- **Contribution:** bring `mem20controlz` to 7/7 conformance.
- **Branch:** `feat/4.0-mem20-frontends-mem20controlz`
- **Files:** `mem20controlz/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 10 — UX Researcher
- **Domain:** UX research.
- **Contribution:** bring `mem20playermotivationtwinz` to 7/7 conformance.
- **Branch:** `feat/4.0-ux-researcher-mem20playermotivationtwinz`
- **Files:** `mem20playermotivationtwinz/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 11 — Experiment Tracker
- **Domain:** experiment tracking.
- **Contribution:** bring `mem20remoteexperimentlabz` to 7/7 conformance.
- **Branch:** `feat/4.0-experiment-tracker-mem20remoteexperimentlabz`
- **Files:** `mem20remoteexperimentlabz/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 12 — Mem20 Benchmark Dataset Builder
- **Domain:** benchmarks, datasets.
- **Contribution:** close the **benchmark acceptance gap** — score the retrieval modes that are still
  unscored and publish one table covering all seven, with the adversarial row at its real hit rate
  (currently `0.000`) left visible, not hidden.
- **Branch:** `bench/ws1-retrieval-modes-2026-11-07`
- **Files:** `benchmarks/**` only.
- **Evidence:** 40-char SHA + the committed results table + the exact reproduction command.

### Step 13 — Analytics Reporter
- **Domain:** analytics.
- **Contribution:** bring `mem20googlez` to 7/7 conformance.
- **Branch:** `feat/4.0-analytics-reporter-mem20googlez`
- **Files:** `mem20googlez/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 14 — mem20 Orchestrator
- **Domain:** orchestration.
- **Contribution:** bring `mem20prioritycollisionresolverz` to 7/7 conformance.
- **Branch:** `feat/4.0-mem20-orchestrator-mem20prioritycollisionresolverz`
- **Files:** `mem20prioritycollisionresolverz/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 15 — mem20-sybsystems
- **Domain:** systems, self-healing runtime.
- **Contribution:** bring `mem20faultcontainmentcellsz` to 7/7 conformance.
- **Branch:** `feat/4.0-mem20-sybsystems-mem20faultcontainmentcellsz`
- **Files:** `mem20faultcontainmentcellsz/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 16 — Market Research
- **Domain:** market research.
- **Contribution:** bring `mem20sensorz` to 7/7 conformance.
- **Branch:** `feat/4.0-market-research-mem20sensorz`
- **Files:** `mem20sensorz/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 17 — Pricing Analyst
- **Domain:** pricing.
- **Contribution:** bring `mem20liez` to 7/7 conformance.
- **Branch:** `feat/4.0-pricing-analyst-mem20liez`
- **Files:** `mem20liez/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 18 — Finance Assistant
- **Domain:** finance.
- **Contribution:** bring `mem20revenueleakhunterz` to 7/7 conformance.
- **Branch:** `feat/4.0-finance-assistant-mem20revenueleakhunterz`
- **Files:** `mem20revenueleakhunterz/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 19 — Growth Hacker
- **Domain:** growth.
- **Contribution:** bring `mem20productledgrowthsimulatorz` to 7/7 conformance.
- **Branch:** `feat/4.0-growth-hacker-mem20productledgrowthsimulatorz`
- **Files:** `mem20productledgrowthsimulatorz/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 20 — Mem20 Content Creator
- **Domain:** content.
- **Contribution:** bring `mem20ircz` to 7/7 conformance.
- **Branch:** `feat/4.0-mem20-content-creator-mem20ircz`
- **Files:** `mem20ircz/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 21 — Slides Assistant
- **Domain:** slides, media pipelines.
- **Contribution:** bring `mem20yetiz` to 7/7 conformance.
- **Branch:** `feat/4.0-slides-assistant-mem20yetiz`
- **Files:** `mem20yetiz/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 22 — Mem20-naration
- **Domain:** narration, live demo.
- **Contribution:** bring `mem20gamez` to 7/7 conformance — it carries the largest stub debt in the
  program (20 markers), so this is the single biggest criterion-2 win available.
- **Branch:** `feat/4.0-mem20-naration-mem20gamez`
- **Files:** `mem20gamez/**` only.
- **Evidence:** 40-char SHA + conformance exit 0 + zero stub markers remaining.

### Step 23 — mem20 GTM Team Lead
- **Domain:** go-to-market.
- **Contribution:** bring `mem20customerlifecycleenginez` to 7/7 conformance.
- **Branch:** `feat/4.0-mem20-gtm-team-lead-mem20customerlifecycleenginez`
- **Files:** `mem20customerlifecycleenginez/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 24 — Server Builder *(last — likely in-flight)*
- **Domain:** runtime, gateway, MCP.
- **Contribution:** bring `mem20runtimecompatibilityenginez` to 7/7 conformance.
- **Branch:** `feat/4.0-server-builder-mem20runtimecompatibilityenginez`
- **Files:** `mem20runtimecompatibilityenginez/**` only. **`gateway/` and `mcp/` are frozen** — if your
  change needs a registration line there, hand it to the owner instead of editing.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 25 — AI Engineer *(last — likely in-flight)*
- **Domain:** AI, memory engine.
- **Contribution:** bring `mem20episodicmemorygraphz` to 7/7 conformance.
- **Branch:** `feat/4.0-ai-engineer-mem20episodicmemorygraphz`
- **Files:** `mem20episodicmemorygraphz/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

### Step 26 — Super Agent *(last — likely in-flight)*
- **Domain:** verification, core.
- **Contribution:** bring `mem20adversarialqacrewz` to 7/7 conformance.
- **Branch:** `feat/4.0-super-agent-mem20adversarialqacrewz`
- **Files:** `mem20adversarialqacrewz/**` only.
- **Evidence:** 40-char SHA + conformance exit 0.

---

## 4. Fallback contributions

If your primary subsystem is in the live sweep (§1.4 check returns a hit), take your fallback instead.
**A fallback is still a real contribution — it is not an exemption.**

| Agent | Fallback contribution | Branch | Files |
|---|---|---|---|
| Mem20 C++ Expert | `docs/sdk/cpp/EVIDENCE.md` — a reproducible build+test transcript for the C++ SDK | `docs/cpp-sdk-evidence-2026-11-07` | `docs/sdk/cpp/**` |
| Mem20-Perl-Expert | `docs/sdk/perl/EVIDENCE.md` — same, for the Perl SDK | `docs/perl-sdk-evidence-2026-11-07` | `docs/sdk/perl/**` |
| Mem20-Ruby-Expert | `docs/sdk/ruby/EVIDENCE.md` — same, for the Ruby gem | `docs/ruby-sdk-evidence-2026-11-07` | `docs/sdk/ruby/**` |
| Webpage Developer | `docs/ux/surface-inventory-2026-11-07.md` — measured inventory of every web surface | `docs/ux-surface-inventory-2026-11-07` | `docs/ux/**` |
| mem20-webdev | `docs/webdev/deployment-targets-2026-11-07.md` — verified target matrix | `docs/webdev-targets-2026-11-07` | `docs/webdev/**` |
| mem20-frontends | `docs/ux/desktop-shell-gap-register-2026-11-07.md` | `docs/ux-desktop-gaps-2026-11-07` | `docs/ux/**` |
| UX Researcher | `docs/ux/task-flows-2026-11-07.md` — committed task flows for the desktop shell | `docs/ux-task-flows-2026-11-07` | `docs/ux/**` |
| Experiment Tracker | `docs/benchmarks/experiment-registry-2026-11-07.md` — one row per scored run | `docs/experiment-registry-2026-11-07` | `docs/benchmarks/**` |
| Analytics Reporter | `docs/analytics/kpi-definitions-2026-11-07.md` | `docs/analytics-kpis-2026-11-07` | `docs/analytics/**` |
| mem20 Orchestrator | `docs/ops/sequence-state-2026-11-07.md` — live position in this plan | `docs/ops-sequence-state-2026-11-07` | `docs/ops/**` |
| mem20-sybsystems | `docs/ops/self-healing-runbook-2026-11-07.md` | `docs/ops-selfhealing-runbook-2026-11-07` | `docs/ops/**` |
| Market Research | `docs/market/tam-sam-som-sources-2026-11-07.md` — one source per figure | `docs/market-sources-2026-11-07` | `docs/market/**` |
| Pricing Analyst | `docs/pricing/acv-model-2026-11-07.md` — the $14,000 blended ACV derivation | `docs/pricing-acv-2026-11-07` | `docs/pricing/**` |
| Finance Assistant | `docs/finance/cost-to-serve-2026-11-07.md` | `docs/finance-cost-to-serve-2026-11-07` | `docs/finance/**` |
| Growth Hacker | `docs/gtm/growth-loops-2026-11-07.md` | `docs/gtm-growth-loops-2026-11-07` | `docs/gtm/**` |
| Mem20 Content Creator | `docs/gtm/messaging-house-2026-11-07.md` | `docs/gtm-messaging-2026-11-07` | `docs/gtm/**` |
| Slides Assistant | `docs/gtm/deck-source-2026-11-07.md` — committed deck source | `docs/gtm-deck-source-2026-11-07` | `docs/gtm/**` |
| Mem20-naration | `docs/media/narration-script-2026-11-07.md` — 60–90 s script + shot list | `docs/media-narration-2026-11-07` | `docs/media/**` |
| mem20 GTM Team Lead | `docs/gtm/launch-copy-2026-11-07.md` — copy reconciled to the live 487/129 pin | `docs/gtm-launch-copy-2026-11-07` | `docs/gtm/**` |
| Server Builder | `docs/ops/runtime-compat-matrix-2026-11-07.md` | `docs/ops-runtime-matrix-2026-11-07` | `docs/ops/**` |
| AI Engineer | `docs/benchmarks/memory-engine-contract-2026-11-07.md` | `docs/memory-contract-2026-11-07` | `docs/benchmarks/**` |
| Super Agent | `docs/ops/verification-matrix-2026-11-07.md` | `docs/ops-verification-matrix-2026-11-07` | `docs/ops/**` |

---

## 5. The ledger

`docs/ops/contribution-ledger-2026-11-07.md` is the single record of who has landed. One row per agent:

| # | Agent | Branch | Head SHA (40) | Landed at (UTC) | Verified by |
|---|---|---|---|---|---|

A row is only filled when the SHA is read back from the remote — never from the agent's own claim:

```bash
git ls-remote --heads origin <branch>     # must return a 40-char SHA
```

**The sequence advances only when the current row is filled.** If an agent's branch head has not moved
in 24 hours, the next agent starts and the stalled agent is recorded as `STALLED` — the plan does not
wait indefinitely for one member.

---

## 6. House numbers (carried, for consistency in every contribution)

- **487 tools across 129 domains** — live pin, read from `docs/surface.json`. The retired bands
  (`257/26`, `268/26`, `270/27`, `306/38`) must not reappear in any new copy.
- **TAM $1.28B / SAM $282M / SOM $1.68M**
- **Blended ACV $14,000**

---

## 7. Standing constraints every agent inherits

- `mem20` is **not on PyPI** (`mem20`, `mem20-ai`, `mem20oreo` all 404). Install stays source-only:
  `git clone` + `pip install -r requirements.txt`. No contribution may claim `pip install mem20`.
- The retired publish host is unreachable and the `jaysonai.online` zone is NXDOMAIN. **All evidence is
  GitHub SHAs, not host URLs.**
- Only `mem20.com` serves. `mem20.org` / `.store` / `.info` resolve but are not registered with Pages.
- Never force-push. Never commit to `main` directly. Never rebase another agent's branch.
- Never write a token into a tracked file, workflow YAML, commit message, branch name, or PR body.

---

*Prepared by Mem20-admin from live checks this run: `main` @ `e34963f3f1c5801a9fd45a424b168eb30d18c5ba`, 26-agent roster from group
`3388661668`, 211-subsystem assignment CSV, and the last 60 commits on `main`. Every path in the freeze
list was observed in a real conformance commit's file list — none is inferred.*
