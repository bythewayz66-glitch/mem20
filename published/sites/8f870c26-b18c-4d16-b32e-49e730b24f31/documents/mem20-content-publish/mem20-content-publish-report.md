# mem20 Content — Canonical Repo Refresh + Gabe Publish Report (v3)

**Prepared by:** Mem20-Content (Content Creator) · **Program:** mem20 launch / repo migration
**Owner:** bythewayz66 · **Date:** 2026-10-14
**Publish leg:** sidney (root@216.198.115.91:2222) via **gabe** — the sole publish authority
**Scope:** long-form articles, launch copy, README/docs rewrites, Show HN / Product Hunt posts, landing copy, social threads.

---

## 1. What this run did

The canonical repository moved. Every content asset now points at the **single canonical
repo** and nothing else:

> **`https://github.com/bythewayz66-glitch/mem20`** — branch `main`, MIT, v2.1.0rc2, **270 tools across 27 domains**, protocol 2025-06-18.

This supersedes the earlier v2 pack, which (a) still contained the retired repository
string in live clone URLs and (b) hedged the canonical target as "pending". The canonical
repo is now **live and verified**; there is no longer any reason for an asset to name a
second repository.

---

## 2. Live verification (performed this run)

Each status below was observed by curl in this run — not asserted from memory.

| Reference | Check | Observed | Verdict |
|---|---|---|---|
| `https://github.com/bythewayz66-glitch/mem20` | GitHub REST API | **200** (public) | ✅ canonical, live |
| the retired predecessor repository | GitHub REST API | **404** | ⛔ retired — not republished |
| `https://pypi.org/pypi/mem20/json` | PyPI JSON API | **404** | ⚠️ the registry install is NOT a working command |
| the historical source repository | GitHub REST API | **200** | ✅ exists (retired v1.0.1 source) |

**Canonical repo head:** `main` @ `c274404a116f203b0f...` (marker commit published by GitHub Repo Assistant).
**Tool surface:** **270 tools across 27 domains** — the `verify_mcp.py` handshake count (268 domain tools + 2 infra tools); `docs/TOOL-DOMAINS.md` names all 270 by source module.

---

## 3. Stale → new ledger (the single source of truth)

| # | Was (retired) | Now (canonical) | Why |
|---|---|---|---|
| 1 | the retired repo used as a **live clone/repo URL** | `github.com/bythewayz66-glitch/mem20` | The retired repo **404s**; the canonical one is **200**. |
| 2 | Canonical target described as *"being published / pending"* | Canonical repo stated as **live** | It is published now. |
| 3 | A second, historical repository named as "the verified live source" in **live** copy | **No second repository named anywhere a reader could act on it.** Only the canonical repo appears in actionable copy. | A published asset must not point a reader at a retired URL, and must not compete with the canonical repo. |
| 4 | Install block: clone + venv + a contradicting dependency pin + editable install + a module path from the old substrate repo | Real repo install: `git clone …/mem20.git` → `cd mem20` → `pip install -e .` (deps resolve into the current interpreter). Runtime entry point `mem20-mcp`. | **Verified against the canonical repo's own files:** `pyproject.toml` declares `dependencies = ["mcp>=2.1.1", "pydantic>=2.13.4", …]` and `[project.scripts] mem20-mcp = "launcher:main"`. There is **no `mcp_cognitive_substrate` module** and **no contradicting pin** in the canonical repo — the v2 block would not work against it. |
| 5 | `~258` / `~258–260` tool counts (v1) | **270 tools / 27 domains** | Re-derived from the repo: 268 domain tools + 2 infra tools. The interim 268/26 figure is retired. |
| 6 | a bare registry install shown as an install command | **Removed.** All assets say the package *"is not yet published to PyPI"* + source install. | PyPI **404**. |

---

## 4. Guardrails preserved (unchanged, re-verified)

- **No LoCoMo/LongMemEval claim.** mem20 has no published benchmark comparable to Mem0 or Zep; assets say so explicitly.
- **Adversarial-retrieval weakness disclosed** wherever limits are discussed — framed as a known weakness with a roadmap. (No numeric benchmark figures are published anywhere: no LoCoMo/LongMemEval-comparable data exists for mem20, and we do not present unverifiable numbers.)
- **Promotion described as "evidence-based with an append-only audit trail"** — never *tamper-proof*, never *unfakeable*.
- **No competitor disparagement** — the category answer ("they optimize retrieval; nobody leads with auditability") is used, their numbers are not attacked.
- **No banned phrasings:** "provably secure", "tamper-proof memory", "matches Mem0", "beats Zep", "industry-leading retrieval", unqualified superlatives.

---

## 5. Assets in this refresh set (v3)

| Asset | What it is | File |
|---|---|---|
| **Content publish report** (this file) | Stale→new ledger, live checks, guardrails, publish records | `mem20-content-publish-report.md` |
| **README / docs install block** | Repo H1 + badges, install, run, MCP client config, benchmarks + limits | `readme-install-block.md` |
| **Launch copy pack** | One-liner, HN/PH/LinkedIn/X variants, value bullets, claim ledger, guardrails | `mem20-launch-copy.md` |
| **Show HN post** | Publish-ready title + body + comment strategy | `show-hn-post.md` |
| **Product Hunt post** | Tagline, description, maker comment, topics | `product-hunt-post.md` |
| **Social threads** | X single + 6-post thread, LinkedIn, 3 Reddit variants | `social-threads.md` |
| **Long-form article** | ~1,400-word dev.to/Medium deep-dive | `long-form-article.md` |
| **Landing-page copy update** | Exact string corrections for the live launch page | `landing-page-copy-update.md` |
| **Reference audit (CSV)** | Context-aware, per-asset, per-rule machine audit | `mem20-reference-audit.csv` |
| **Asset catalogue** | Self-contained catalogue of the whole asset set (HTML source, printed in full in the pack) | `mem20-content-catalog.html` |

---

## 6. Open items (honest, not copy problems)

1. **The registry install is unpublished** (PyPI 404). When it goes live, swap the source block for the pip command in: launch copy pack, README block, Show HN post, long-form article.
2. **Posting is manual.** No HN/X/GitHub/Reddit integration is configured; all posts are paste-ready.
3. **Repo-asset breadcrumb:** the migration record intentionally retains one **Was / Now** reference to the retired repo string, because a migration table that omits the old value is not an accurate record. It is labelled as retired, never as a live URL.

**Where this pack lives (published destination):** the combined asset pack is published to the
sidney live surface through gabe. gabe writes a flat filename into the live root, so the pack's
on-host live path is:

```
/opt/mem20/live/mem20-content-asset-pack.md
```

Every actionable and tracking link inside the pack points at the canonical repository
(`https://github.com/bythewayz66-glitch/mem20`). The pack carries no external hosting URL of its own.

---

*Prepared by Mem20-Content · published to the sidney live surface through gabe (sole publish authority).*
