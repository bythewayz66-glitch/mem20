# Owner directive — 2026-11-01: verified gap register + 22-agent assignment roster

**Issued by:** bythewayz66 (owner) · **Executed by:** mem20 Orchestrator
**Verified against:** `main` = `2ea4492209dfaae6afb22ca884132a0d1849bfcf` (pushed 2026-11-01T13:21:47Z)
**Repo of record:** `bythewayz66-glitch/mem20` (public). `JaysonAIOnline/mem20` returns **404** — it is not the live repo.

> **Standing rule (owner, restated):** a deliverable exists only as a **commit SHA on a pushed branch**
> or a **permanent URL committed under `docs/`**. Chat-only claims do not count and will be scored as absent.

---

## 1. DNS verification — the owner's claim is CORRECT

Two independent DoH resolvers, queried this run: Cloudflare (`cloudflare-dns.com/dns-query`) and
Google (`dns.google/resolve`). Status `0` = NOERROR.

| Name | Type | Cloudflare | Google | Answer |
|---|---|---|---|---|
| `mem20.com` | A | 0 | 0 | 185.199.108.153 / .109 / .110 / .111 |
| `mem20.org` | A | 0 | 0 | 185.199.108.153 / .109 / .110 / .111 |
| `mem20.store` | A | 0 | 0 | 185.199.108.153 / .109 / .110 / .111 |
| `mem20.info` | A | 0 | 0 | 185.199.108.153 / .109 / .110 / .111 |
| `www.mem20.com` | CNAME | 0 | 0 | `bythewayz66-glitch.github.io.` |
| `www.mem20.org` | CNAME | 0 | 0 | `bythewayz66-glitch.github.io.` |
| `www.mem20.store` | CNAME | 0 | 0 | `bythewayz66-glitch.github.io.` |
| `www.mem20.info` | CNAME | 0 | 0 | `bythewayz66-glitch.github.io.` |
| `mem20.jaysonai.online` | A/CNAME | **3 (NXDOMAIN)** | **3 (NXDOMAIN)** | none |

**Conclusion: no DNS record is missing for the four custom domains.** All four apexes carry the full
four-address GitHub Pages A set and all four `www` names carry the correct CNAME. No IONOS write is
warranted, and none was performed.

### 1a. The gap is registration, not DNS

| Host | HTTP | Bytes | Meaning |
|---|---|---|---|
| `https://mem20.com/` | **200** | 33,429 | live, real page |
| `https://www.mem20.com/` | 301 | 162 | → `https://mem20.com/` |
| `https://mem20.org/` | 404 | 9,115 | GitHub "Site not found" — **not registered** |
| `https://mem20.store/` | 404 | 9,115 | GitHub "Site not found" — **not registered** |
| `https://mem20.info/` | 404 | 9,115 | GitHub "Site not found" — **not registered** |
| `https://www.mem20.org/` | 404 | 9,115 | same |
| `https://www.mem20.store/` | 000 | 0 | TLS handshake fails (no cert issued) |
| `https://www.mem20.info/` | 000 | 0 | TLS handshake fails (no cert issued) |

A 9,115-byte 404 is GitHub's own "Site not found" page. GitHub Pages allows **exactly one custom
domain per repository**; `docs/CNAME` contains `mem20.com`, so `.org` / `.store` / `.info` resolve
correctly but are not served. This is a registration/redirect-layer fact, not a DNS bug.

### 1b. `mem20.jaysonai.online` cannot be fixed with the IONOS token

`jaysonai.online` is delegated to **Cloudflare** nameservers (`ainsley.ns.cloudflare.com`,
`quentin.ns.cloudflare.com`), not IONOS. The IONOS DNS API has no authority over that zone. The
hostname is also being deliberately retired (`docs/ws1-retire-jaysonai-hostname`,
`080fdda1df70920993d272ed43d8848fe7830875`). **Recommendation: do not create it.**

---

## 2. Verified gap register

| # | Gap | Evidence (this run) |
|---|---|---|
| G1 | **`Tests` check is RED on main** | 14 check-runs on `2ea44922`: 13 `success`, 1 `failure` (`Tests`, id `124860549243`). Annotation: `.github` line 32, "Process completed with exit code 4" — the *Compute diff against the base* step in `.github/workflows/ci.yml`. |
| G2 | **13 merged-but-undeleted branches** | 13 non-`main` heads; `git merge-base --is-ancestor` returns true for **all 13** → 0 unmerged, 13 stale refs. |
| G3 | **Launch artifacts stale on version** | `docs/index.html` and the served `https://mem20.com/` both contain `270 tools` ×8, `27 domains` ×8, and **`v3.0.0` ×4** — while `VERSION` = `3.1.0` and tag `v3.1.1` exists. |
| G4 | **Tag is 63 commits stale** | `compare/v3.1.1...main` → `ahead_by 63`, `behind_by 0`. `v3.1.0` → 62. |
| G5 | **PyPI 404s** | `pypi.org/pypi/mem20/json` → 404; `mem20-mcp` → 404; `mem20-sdk` → 404. |
| G6 | **Three domains unregistered** | §1a — `.org` / `.store` / `.info` return GitHub 9,115-byte 404. |
| G7 | **Chronicle is 5 days stale** | `docs/app/narrative/serial-2026-10-27.md` is the **only** narrative file; pinned to frontier `e7758bd178d38da63c5359dded0aada8bfc0eea5`; contains **0** occurrences of `2ea4492`, **0** of `3.1.0`, **0** of `Sidney`, **0** of `gabe`. |
| G8 | **Retired infra still on main** | `docs/ops/branch-inventory-2026-10-31.md` §227: retired identities (`Sidney`, `gabe`, `jaysonai`) **still present on `main`** after PR #145. |
| G9 | **Benchmark quality gaps** | `benchmarks/results/latest.md` + `latest.json` on main; adversarial_hard and unanswerable slices still need a scored, reproducible row. |
| G10 | **`/sites/` anonymous 403** | Artifact URLs are project-member-only; no anonymous-reachable launch URL exists. |

---

## 3. Assignment roster — 22 agents

Each row: **owner** · **gap** · **task** · **acceptance evidence**.

### Engineering / repo

**1. GitHub Repo Assistant** — G1, G2, G4
- Fix the red `Tests` check: reproduce `exit code 4` from the *Compute diff against the base* step in `.github/workflows/ci.yml` on `2ea44922`, fix the step (not the test), and get `Tests` green on a pushed branch.
- Delete the 13 merged refs listed in §2/G2 (all are ancestors of main — zero risk).
- Re-tag `v3.1.1` at current main (or cut `v3.1.2`) so the tag is not 63 commits behind.
- **Acceptance:** branch SHA with `Tests` = `success` in check-runs; `git ls-remote --heads` shows only `main`; `compare/<newtag>...main` → `ahead_by 0`.

**2. mem20-webdev** — G6, G10
- DNS is already correct (§1) — **do not touch IONOS**. Build the redirect layer for `.org` / `.store` / `.info` (per-host rules in front of Pages, or a small redirect service), and document the one-custom-domain-per-repo constraint.
- **Acceptance:** committed `docs/webdev/domain-routing-2026-11-01.md` with a per-host table and a `curl -sI` transcript showing each host's real status; no claim of 200 without a captured response.

**3. Webpage Developer** — G3
- Rebuild `docs/index.html` so version strings read `3.1.0` (or `3.1.1`), keeping `270 tools` / `27 domains`. Purge all four `v3.0.0` occurrences.
- **Acceptance:** branch SHA; `grep -c 'v3.0.0' docs/index.html` → `0`; `grep -c '270 tools'` → non-zero; served `https://mem20.com/` re-checked after Pages rebuild.

**4. mem20-frontends** — G3
- Audit every frontend surface (`web/src/**`, `docs/dashboard.html`) for stale counts/versions; produce a drift table and fix the code paths.
- **Acceptance:** committed `docs/webdev/frontend-drift-2026-11-01.md` + branch SHA with fixes.

**5. Server Builder** — G8
- Purge retired `Sidney` / `gabe` / `jaysonai` references from `main` (they survived PR #145 by design). Verify no live service still points at them.
- **Acceptance:** branch SHA; `git grep -ciE 'sidney|gabe'` on the branch → `0` outside an explicit historical/attribution allowlist you document.

**6. mem20-sybsystems** — G1
- Independent second opinion on the `Tests` failure: run the suite locally at `2ea44922`, capture the real failing assertion, and file a defect list with repro steps.
- **Acceptance:** committed `docs/ops/tests-failure-repro-2026-11-01.md` with the command, exit code, and failing test names.

**7. AI Engineer** — G9
- Own the retrieval-quality question behind the adversarial slices: explain *why* adversarial_hard and unanswerable score low, and propose a concrete retrieval change with a measurable target.
- **Acceptance:** committed `docs/benchmarks/retrieval-gap-analysis-2026-11-01.md` citing `benchmarks/results/latest.json` rows by name.

**8. Experiment Tracker** — G9
- Extend `docs/benchmarks/experiment-registry.md` + `experiments.json` to record which retrieval modes are scored vs unscored for the 2026-10-31 four-mode run, keeping the adversarial 0.000 row visible.
- **Acceptance:** branch SHA; registry row count matches the modes actually present in `benchmarks/results/latest.json`.

**9. Mem20 Benchmark Dataset Builder** — G9
- Close the adversarial_hard and unanswerable quality gaps: publish a scored, reproducible row for each, with the harness command and dataset manifest.
- **Acceptance:** branch SHA touching `benchmarks/results/latest.{md,json}`; every new row reproducible from a documented command; no row published without a run.

### SDKs

**10. Mem20-Perl-Expert** — G5
- Perl SDK is on main (`sdk/perl/**`, incl. `t/05-surface.t`). Get it to a publishable state and document the CPAN path; verify the surface guard still passes.
- **Acceptance:** branch SHA; `prove -l t/` transcript committed; `docs/sdk/perl-release-2026-11-01.md`.

**11. Mem20-Ruby-Expert** — G5
- Ruby SDK (`mem20-sdk-ruby/**`) — same: gemspec, packaging, and a green `rspec` run.
- **Acceptance:** branch SHA; committed rspec summary; `docs/sdk/ruby-release-2026-11-01.md`.

**12. Mem20 C++ Expert** — G5
- C++ SDK (`sdk/cpp/**`) — CMake install/export config and a green `ctest` run; `test_surface_docs.cpp` must pass.
- **Acceptance:** branch SHA; committed `ctest` output; `docs/sdk/cpp-release-2026-11-01.md`.

### Content / GTM

**13. Mem20 Content Creator** — G3
- Rewrite launch copy to the verified surface: **270 tools / 27 domains / v3.1.0**, auditable agent memory, TAM $1.28B / SAM $282M / SOM $1.68M / ACV $14,000. No unverified benchmark claims.
- **Acceptance:** branch SHA under `docs/gtm/`; every number traceable to `README.md` or `VERSION`.

**14. mem20 GTM Team Lead** — G3
- Reconcile `docs/gtm/claim-ledger.md` against main: mark each claim verified/stale with the command that settles it.
- **Acceptance:** branch SHA; ledger has zero rows marked `verified` without a cited command.

**15. Growth Hacker** — G10
- Build the launch-channel plan (Show HN / Product Hunt / Reddit) gated on a real anonymous-reachable URL — currently blocked by G10. Deliver the plan plus the exact unblock condition.
- **Acceptance:** committed `docs/gtm/launch-channels-2026-11-01.md` naming the blocker explicitly.

**16. Market Research** — positioning
- Refresh the competitive matrix against the current surface; keep TAM/SAM/SOM sourced.
- **Acceptance:** branch SHA under `docs/market/`; every figure carries a source.

**17. Pricing Analyst** — ACV
- Re-derive tier pricing from blended ACV $14,000 and reconcile `docs/pricing/RECONCILIATION_NOTE.md` with the 270/27 surface.
- **Acceptance:** branch SHA; arithmetic shown, not asserted.

**18. Finance Assistant** — claims
- Re-run the finance claim check (`chore/finance-claims-check` is already merged) and confirm `docs/finance/CLAIMS_CHECK_H18.md` has no stale 258/260 or 26-domain figures.
- **Acceptance:** branch SHA; `grep -c '258 tools\|260 tools\|26 domains'` → `0` in that file.

**19. Slides Assistant** — G3
- Rebuild the investor deck to v3.1.0 / 270 / 27; the deck was already restored once (`a36a34a`), so verify the PERMANENT_URL record is intact.
- **Acceptance:** branch SHA; committed deck with a working permanent URL.

**20. UX Researcher** — desktop
- Advance the mem20 desktop research: personas + task flows grounded in the actual `web/src/views/**` surfaces that exist.
- **Acceptance:** branch SHA under `docs/ux/`; each flow names a real view file.

**21. Analytics Reporter** — G1
- Build the program scoreboard from real signals: check-run pass rate on main, branch count, tag distance, PyPI status. No invented metrics.
- **Acceptance:** branch SHA under `docs/ops/`; every number reproducible by a stated command.

**22. Mem20-naration** — G7
- Bring the chronicle series current. `serial-2026-10-27.md` stops at frontier `e7758bd`; publish the next instalments covering: main `2ea44922`, 270 tools / 27 domains, `VERSION` 3.1.0 + tag v3.1.1, the at-risk convergence **10 → 3 → 0** (`docs/ops/branch-inventory-2026-10-31.md` §196), and the retirement of the Sidney/gabe infra.
- **Acceptance:** new files under `docs/app/narrative/` committed on a branch, each pinned to a real baseline SHA and citing the command behind every figure.

**23. Mem20-admin** — coordination
- Score the roster at deadline: for each of the 22 rows, record DELIVERED / ABSENT with the SHA or URL. Chat claims score as ABSENT.
- **Acceptance:** committed `docs/ops/roster-score-2026-11-01.md` with 22 rows and a SHA per DELIVERED row.

---

## 4. What the owner needs to decide

1. **Which domain becomes primary?** Only one can be registered on Pages. `mem20.com` is live; promoting `.org`/`.store`/`.info` takes `mem20.com` offline for the duration of certificate issuance.
2. **`mem20.jaysonai.online`** — confirm retirement (recommended) or supply a Cloudflare token, since IONOS has no authority over that zone.
3. **PyPI publishing** — G5 needs a PyPI token/trusted-publisher setup; no agent can close it without credentials.

---

*Verified 2026-11-01 by mem20 Orchestrator. Every figure above was produced by a command or HTTP
request in this run; nothing is quoted from an earlier report without re-checking it.*
