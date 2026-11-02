# mem20 workload roster — 2026-11-01 (owner directive, wave 2)

**Issued by:** Mem20-admin · **Group:** sidney (3388661668)
**Baseline `main`:** `2ea4492209dfaae6afb22ca884132a0d1849bfcf` (2026-11-01 06:20:25 -0700, `docs(bench): land four-mode retrieval benchmark results for 2026-10-31`)
**Tracked files:** 8,536 · **VERSION:** 3.1.0 · **Open PRs:** 0 · **Open issues:** 0
**At-risk commits (sum of branch `ahead`):** 1 — `docs/ws1-owner-directive-2026-11-01` only; all other 13 refs are `ahead=0` (already merged, deletable)
**Deadline:** 2026-11-02T06:00:00Z = 2026-11-01 23:00 MST
**Evidence rule:** a 40-char commit SHA on a pushed branch, or a `/sites/` permanent URL committed under `docs/`. **A chat message does not count.**

Every figure below was measured in this run. Rows citing a defect cite the command output that found it.

---

## 1. Corrections to the directive itself (audited, not transcribed)

| Directive item | Finding | Evidence |
|---|---|---|
| "Rebuild the stale `mem20-launch-v2` page" | **True.** 4× `257 tools across 26 domains`, 1× `257 tools · 26 domains`, 6× `v2.1.0rc2` in `published/sites/f7c01331-…/webpages/mem20-launch_v2/index.html` | `grep -c` on that path |
| "Bump launch-v5's v3.0.0 badge to 3.1.0" | **There is no `launch_v5` in the repo.** The canonical page is `docs/index.html` (4× `v3.0.0`, already 270/27) — the live `mem20.com` page. Treated as launch-v5. | `git ls-files \| grep launch_v5` → no rows; `ls` shows launch, launch_v2, launch_v3, launch_v4 only |
| A prior report's claim that `mcp-types` is a missing dependency | **Investigated and rejected.** `mcp-types` returns **HTTP 200 on PyPI** and the module simply is not installed in this sandbox. Not a repo defect — not assigned. | `curl pypi.org/pypi/mcp-types/json` → 200 |

Both items 1 and 2 were **executed by Mem20-admin** in this run (see §4).

---

## 2. Assignment table — 24 agents

| # | Agent | Branch | Real defect cited | Deliverable / acceptance |
|---|---|---|---|---|
| 1 | Server Builder | `fix/ws2-tests-green` | `Tests` check = **failure** on main HEAD `2ea44922`; 13 of 14 checks green | Root-cause the red `Tests` run and land the fix. Acceptance: check run on the new head shows `Tests → success`; quote SHA |
| 2 | GitHub Repo Assistant | `chore/ws2-tag-3-1-2` | `v3.1.1` = `52ffe13d0460` is **63 commits behind** main; no tag equals HEAD; 84 tags (79 `archive-*`) | Cut `v3.1.2` at main HEAD and record the tag→SHA. Acceptance: tag object SHA + target SHA both quoted |
| 3 | Webpage Developer | `feat/ws2-launch-canon` | Live `mem20.com` is `docs/index.html`; 4 `webpages/` copies still carry `257 tools` (`mem20-prototype` ×9, `design-research` ×5+6, `market-research-v3` ×5, `launch_v3` ×4, `launch_v4` ×4) | One canonical launch page on 270/27 with a `PROVENANCE.md`; retire or redirect the stale copies. Acceptance: committed `docs/sites/launch-canonical.md` naming the canonical path + SHA |
| 4 | mem20-webdev | `chore/ws2-ref-prune` | 13 branches at `ahead=0` (merge-base confirmed ancestors), tips 31–66 behind | Delete the 13 merged refs; archive-tag anything unmerged. Acceptance: `chore/ws2-ref-prune` carries the before/after ref list + SHA |
| 5 | Mem20 Content Creator | `docs/ws2-content-r270` | Long-form + launch copy mix 257/268/270 across `published/content/mem20-long-form-v3/` | Rewrite all narrative to 270/27, v3.1.0, source-only install. Acceptance: committed copy file + SHA |
| 6 | mem20 GTM Team Lead | `docs/ws2-gtm-claim-ledger` | `docs/gtm/claim-ledger.md` **contradicts itself at this HEAD**: 3× `257 tools`, 6× `270 tools`, 3× `26 domains`, 11× `27 domains` | Make the ledger single-valued. Acceptance: `grep` count = one value only, committed + SHA |
| 7 | Market Research | `docs/ws2-market-sources` | TAM/SAM/SOM carried, never re-derived (`docs/finance/inputs.json` `provenance` says so) | Add a per-figure source citation for $1.28B / $282M / $1.68M. Acceptance: committed source table + SHA |
| 8 | Pricing Analyst | `docs/ws2-pricing-acv` | ACV $14,000 carried, not derived; `docs/pricing/RECONCILIATION_NOTE.md` is the stated source | Build the blended-ACV arithmetic from the tier ladder. Acceptance: committed model + SHA |
| 9 | Finance Assistant | `docs/ws2-finance-inputs` | `docs/finance/inputs.json` `as_of` = **2026-10-26** — six days stale | Refresh `as_of` against this HEAD, keep TAM/SAM/SOM verbatim. Acceptance: committed JSON + SHA |
| 10 | Mem20 Benchmark Dataset Builder | `bench/ws2-adversarial` | `benchmarks/results/latest.md`: `adversarial_hard` 0.025–0.050, `unanswerable` **0.000** in every mode | Improve or explicitly document the adversarial ceiling. Acceptance: updated `latest.md` + reproduction command + SHA |
| 11 | Experiment Tracker | `docs/ws2-bench-registry` | 10 mode labels in `latest.md`, no run registry | Register every run with config + result. Acceptance: committed registry + SHA |
| 12 | AI Engineer | `docs/ws2-adversarial-probe` | Same 0.000 unanswerable row — needs a cause, not a number | Diagnose why every mode scores 0.000 on unanswerable. Acceptance: committed findings + SHA |
| 13 | UX Researcher | `docs/ws2-design-controlz` | `docs/design/` **does not exist** at this HEAD | Task flows + wireframes for mem20controlz. Acceptance: committed tree + SHA |
| 14 | Analytics Reporter | `docs/ws2-analytics-kpis` | `docs/analytics/` **does not exist** at this HEAD | KPI definitions tied to the ledger fields. Acceptance: committed file + SHA |
| 15 | Mem20-naration | `docs/ws2-chronicle` | `published/chronicles/` **does not exist**; last serial post is **2026-10-27**, five days stale (`fbdfa711`) | Chronicle 2026-10-28 → 11-01. Acceptance: committed file covering each date that actually landed work + SHA |
| 16 | Mem20 C++ Expert | `chore/ws2-cpp-surface-ci` | `sdk/cpp/README.md` mixes 1× `257 tools` with 3× `270 tools`; `test_surface_docs.cpp` 1× vs 2× | Reconcile + add ctest to CI. Acceptance: committed fix + CI job + SHA |
| 17 | Mem20-Perl-Expert | `chore/ws2-perl-surface` | `sdk/perl/AUDIT.md` asserts 270/27 but nothing enforces it | Add an enforced surface check. Acceptance: committed test/script + SHA |
| 18 | Mem20-Ruby-Expert | `chore/ws2-ruby-relocate` | Ruby SDK lives at repo root (`mem20-sdk-ruby/`), not under `sdk/` where cpp+perl are | Relocate to `sdk/ruby/` or document the deviation; keep `ruby-sdk.yml` green. Acceptance: committed move + SHA |
| 19 | mem20-sybsystems | `chore/ws2-sbom` | No SBOM artifact on a 270-tool, 8,536-file surface | Generate + commit an SBOM. Acceptance: committed SBOM + SHA |
| 20 | Growth Hacker | `docs/ws2-growth-plan` | Zero distribution assets beyond the site | Concrete growth plan with tracked links. Acceptance: committed plan + SHA |
| 21 | Super Agent | `chore/ws2-artifact-gate` | No artifact-evidence gate in `.github/workflows/` (grep for `evidence` → 0 hits) | Add a CI gate requiring a committed artifact or permanent URL per PR. Acceptance: committed workflow + SHA |
| 22 | mem20 Orchestrator | — | Coordination | Owns sequencing + the 23:00 MST checkpoint |
| 23 | mem20-frontends | — | **Director role this wave**, no code row | Reviews rows 1–21 for overlap; no branch of its own |
| 24 | Slides Assistant | — | **Director role this wave**, no code row | Reviews deck placement against row 21's gate |
| — | Mem20-admin | own slice | Verification only | Re-verifies every claimed SHA at 06:00Z; files the ledger |

---

## 3. Already landed (not to be re-done — dropped from assignments)

| Item | Proof |
|---|---|
| 13 of the 14-branch backlog converged | every ref except one returns `ahead=0` |
| Release lane moved off v3.0.0 | `v3.1.1` @ `52ffe13d0460` exists |
| Canonical page already 270/27 | `docs/index.html` — 5× `270 tools across 27 domains` |
| Benchmark harness already multi-mode | `benchmarks/results/latest.md` carries 10 mode labels |

---

## 4. Mem20-admin's own slice — completed this run

| Item | What was done | Evidence |
|---|---|---|
| Rebuild `mem20-launch_v2` → 270/27 | Rebuilt in place as `webpages/mem20-launch_v2_r270/` | 0× `257`, 0× `v2.1.0rc2`, 4× `270 tools`, 6× `v3.1.0`; sha256 `8de01f2a7626…`; 40,709 B |
| Bump launch-v5 badge → 3.1.0 | Rebuilt `docs/index.html` as `webpages/mem20-launch_v5_r311/` | 0× `v3.0.0`, 4× `v3.1.0`; sha256 `1b176cebd17d…`; 33,429 B |

Both live at `/sites/b5d558be-…`, verified by fetching back and re-grepping the served bytes.

---

## 5. Standing corrections carried forward

- **House numbers:** 270 tools / 27 domains (257/26 and 268/26 are retired). TAM $1.28B / SAM $282M / SOM $1.68M; blended ACV $14,000.
- **Directly measured this run:** `mcp/`-scoped `self.tools["…"]` = **270**; repo-wide = **271** (one registration outside the server tree); `mcp/tools/*.py` = **27**. The scoped count is authoritative.
- **`mem20.jaysonai.online`** is NXDOMAIN on Cloudflare **and** Google DoH (Status 3) with the zone's own SOA in Authority while the apex returns Status 0 — a **missing record, not propagation**. Record to create: **CNAME `mem20` → `bythewayz66-glitch.github.io`, proxy OFF, TTL Auto.**
- **Sidney `216.198.115.91`** is unreachable: errno 113 on 2222/9900, timeout on 22/80/443. Hermes gateway does not answer. Unreachable from this sandbox ≠ powered off.
