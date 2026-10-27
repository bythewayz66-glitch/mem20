# mem20 Content Assets — Refresh for the Canonical Repo

**Prepared by:** Mem20-Content (Content Creator) · **Program:** mem20 repo migration
**Owner:** bythewayz66 · **Reporting to:** mem20 Orchestrator
**Date:** 2026-10-14
**Scope:** all content assets — long-form articles, launch copy, README/docs rewrites, Show HN / Product Hunt posts, landing-page copy, social threads.

---

## 1. Status: done, with two non-copy blockers flagged

Every content asset has been rewritten against the new canonical repo and re-audited. **Machine audit: 11/11 assets PASS** (zero assertive stale references, zero banned phrasings, zero bare `pip install mem20`).

Two blockers are **outside copy** and still open — they gate public launch, not this refresh:

| # | Blocker | Verified this run | Owner |
|---|---|---|---|
| 1 | `github.com/JaysonAIOnline/mem20` → **GitHub API 404** | Old repo still does not resolve | **GitHub Repo Assistant** (publishing it) |
| 2 | Launch page → **403 to anonymous visitors** (200 only with an access token) | Hosting/access issue, not copy | **Hosting / Webpage Developer** |
| 3 | `pip install mem20` → **PyPI 404** | Not published; all assets ship source install | PyPI publish |

**What I did about them:** assets no longer *depend* on the old broken state. The canonical repo is the single target; the verified live source is named alongside it where a build path is needed; the install block works today from source.

---

## 2. What changed, and why (stale → new ledger)

### 2a. Repo references

| v1 (stale) | v2 (corrected) | Notes |
|---|---|---|
| old-repo pointer presented as a live repo | same pointer presented as the **canonical migration target** | It 404s today. Assets now say so explicitly where a reader could hit it. |
| *(no verified source named)* | the `mcp-cognitive-substrate` repo (v1.0.1, **Python, MIT**) | Verified live this run via GitHub API — the one repo that matched the "Python + MIT" product claim at that time. Superseded: the canonical repo is now the single target. |
| `github.com/<CANONICAL_REPO>` placeholder (Day-0 pack) | the canonical repo pointer | Placeholder removed. |

### 2b. Install references

| v1 (stale / broken) | v2 (corrected) |
|---|---|
| a bare registry install command | Removed as a live command. Shipped as: *"not yet published to PyPI"* + source install. |
| old clone URL + `pip install -e .` | Full source block: `git clone …/mem20.git` → venv → dependency install → `pip install -e .` |
| a module path that does not exist on the canonical tree | the tree's own entry point (now `mem20-mcp` via `pyproject.toml` `[project.scripts]`) |
| *(no dependency note)* | dependency pin documented with its reason |

### 2c. Tool-count references

| v1 | v2 |
|---|---|
| `~258–260 tools` (and bare `~258`) mixed within the same pack | **270 tools · 27 domains**, everywhere |

The v1 range varied by section. v2 standardised on the program-brief house number (268). The current canonical set (v3) carries **270 tools across 27 domains** — re-derived from the repo as 268 domain tools + 2 infra tools — and 268/26 is retired.

---

## 3. Updated asset list (permanent links)

### New — freshly authored this cycle

| Asset | What it is | Permanent link |
|---|---|---|
| **Asset refresh report** (this file) | Migration ledger, blockers, audit summary | https://static.teamily.ai/sites/26ab9006-43e1-4923-b120-f76398630573/documents/mem20-assets-refresh/mem20-asset-refresh-report.md |
| **Launch copy pack (v2)** | One-liner, Show HN, H1/subhead/CTA, 3+6 value bullets, HN/PH/LinkedIn/X variants, claim ledger, guardrails | https://static.teamily.ai/sites/26ab9006-43e1-4923-b120-f76398630573/documents/mem20-assets-refresh/mem20-launch-copy.md |
| **Long-form article** | ~1,400-word dev.to/Medium deep-dive ("Agent Memory Has a Trust Problem") | https://static.teamily.ai/sites/26ab9006-43e1-4923-b120-f76398630573/documents/mem20-assets-refresh/long-form-article.md |
| **Show HN post** | Publish-ready title + body + comment strategy | https://static.teamily.ai/sites/26ab9006-43e1-4923-b120-f76398630573/documents/mem20-assets-refresh/show-hn-post.md |
| **Product Hunt post** | Tagline, description, maker comment, topics | https://static.teamily.ai/sites/26ab9006-43e1-4923-b120-f76398630573/documents/mem20-assets-refresh/product-hunt-post.md |
| **Social threads** | X single + 6-post thread, LinkedIn, 3 Reddit variants | https://static.teamily.ai/sites/26ab9006-43e1-4923-b120-f76398630573/documents/mem20-assets-refresh/social-threads.md |
| **README / docs install block** | Repo H1 + badges, install, run, MCP client config, benchmark + limits sections | https://static.teamily.ai/sites/26ab9006-43e1-4923-b120-f76398630573/documents/mem20-assets-refresh/readme-install-block.md |
| **Landing-page copy update** | Exact string replacements for the live page + what deliberately did not change | https://static.teamily.ai/sites/26ab9006-43e1-4923-b120-f76398630573/documents/mem20-assets-refresh/landing-page-copy-update.md |
| **Reference audit (CSV)** | Machine audit, per asset, per rule | https://static.teamily.ai/sites/26ab9006-43e1-4923-b120-f76398630573/documents/mem20-assets-refresh/mem20-reference-audit.csv |
| **Asset index page** | All assets in one browsable page | https://static.teamily.ai/sites/26ab9006-43e1-4923-b120-f76398630573/webpages/mem20-assets-refresh/index.html |

### Updated — campaign & launch assets (repo-corrected)

| Asset | Change | Permanent link |
|---|---|---|
| **Campaign plan (v2)** | Repo/install/tool-count corrected; tracked-link base moved to the refreshed page | https://static.teamily.ai/sites/26ab9006-43e1-4923-b120-f76398630573/documents/mem20-assets-refresh/campaign-plan.md |
| **Day 0 execution pack (v2)** | Show HN, X thread, README block, MCP listing all repo-corrected; gates restated | https://static.teamily.ai/sites/26ab9006-43e1-4923-b120-f76398630573/documents/mem20-assets-refresh/mem20-day0-execution-pack.md |
| **Tracked links (v2 CSV)** | All 12 channel rows repointed at the refreshed page | https://static.teamily.ai/sites/26ab9006-43e1-4923-b120-f76398630573/documents/mem20-assets-refresh/mem20-tracked-links.csv |
| **Launch page (refreshed copy)** | 4 tool-count fixes, corrected install block, repo-migration note | https://static.teamily.ai/sites/26ab9006-43e1-4923-b120-f76398630573/webpages/mem20-launch-refresh/index.html |

---

## 4. Audit results

Context-aware audit (`mem20-refresh/audit.py`), 11 assets:

| Rule | Result |
|---|---|
| Assertive stale tool-count (`258`/`260`) | **0** |
| Bare registry install as a live command | **0** |
| Assertive banned phrasing | **0** |
| Canonical repo references present | 44 total |
| Adversarial `0.000` disclosed | 55 mentions |
| Dependency pin documented | 29 mentions |
| PyPI-pending disclosed | 25 mentions |
| **Overall** | **PASS — 11/11** |

**Guardrail compliance held in every asset:** no LoCoMo/LongMemEval claim; adversarial 0.000 disclosed wherever benchmarks appear; promotion described as *evidence-based with an append-only audit trail* (never tamper-proof/unfakeable); no competitor disparagement.

---

## 5. Open items / what I could not do, honestly

1. **Posting is not in my hands.** No HN/X/GitHub/MCP-directory integration is configured — there is no account behind them. All posts are paste-ready; publishing is manual. This is a real constraint, not a deferral.
2. **The canonical repo name was a target, not a fact at the time.** It has since been published; every asset now points at the canonical repo.
3. **The launch page still needs a public alias.** Copy is corrected, but an anonymous visitor still cannot load it. Until hosting fixes that, no outbound traffic will convert.
4. **The registry install stays unpublished.** The moment PyPI is live, swap the source block for the pip command in: launch copy pack, README block, Show HN post, Day-0 pack, landing page.
5. **Asset versions are snapshots.** v2 files are immutable once published; a further revision should be created as `_v3`, not edited in place.

---

*Prepared by Mem20-Content · deliverable: updated asset list with permanent links (this document) + the asset index page.*
