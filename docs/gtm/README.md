# docs/gtm — GTM collateral (v3, current)

**Owner:** mem20 GTM Team Lead · **Captured:** 2026-10-31 · **Repo HEAD:** `f1672473cd19d5926e1df0c80042259d3b4b17ca` · **Version:** 3.1.0
**Canonical repo:** https://github.com/bythewayz66-glitch/mem20
**Canonical public URL:** https://mem20.com (preferred) · https://bythewayz66-glitch.github.io/mem20/

> **Version note.** `VERSION` on `main` reads **3.1.0**; `pyproject.toml` still reads **3.0.0** and the highest tag is **v3.1.1**. Quote **3.1.0** and name the defect — see `claim-ledger.md` §1.1. Do not quote 3.0.0 as current.

This directory is the **git-side source of truth** for mem20 go-to-market collateral. Prior versions lived only on a token-gated CDN (`static.teamily.ai/sites/…`), which returns **403 to anonymous readers** — so a `/sites/`-only asset could not be shared, linked, or cited by anyone outside the room. These files are in the repo so they can be read, diffed and linked.

---

## The set

| File | Seat | What it is |
|---|---|---|
| [`claim-ledger.md`](./claim-ledger.md) | Brand & Positioning / Opportunity & Market | **Read this first.** Every verifiable fact, every command, every withdrawn claim. Nothing ships that isn't in here. |
| [`mem20-launch-copy.md`](./mem20-launch-copy.md) | Brand & Positioning Strategist | One-liner, Show HN post, H1/subhead, value props, HN / Product Hunt / LinkedIn / X variants. |
| [`mem20-campaign-plan.md`](./mem20-campaign-plan.md) | Marketing & Demand Gen / Revenue Analytics | Channel tiers, 12 tracked links, measurement plan, launch sequencing. |
| [`mem20-sales-one-pager.md`](./mem20-sales-one-pager.md) | VP of Sales | Pitch, ICP, objection handling, commercial model, 6-week pilot-to-paid motion. |

---

## The five numbers and states that are current

1. **270 tools across 27 domains.** Live handshake: `python3 verify_mcp.py` → `TOOL_COUNT: 270`. Retired: 257, 258, 268.
2. **Install is source-only.** `git clone` → `pip install -r requirements.txt`. `mem20`, `mem20-ai` and `mem20oreo` all **404** on PyPI. Never imply otherwise.
3. **The public web URLs are `https://mem20.com` and `https://bythewayz66-glitch.github.io/mem20/`** — both HTTP 200, both md5 `37246f8d13b0f6870faa913c0a44c68d`, byte-identical to `docs/index.html` (33,429 bytes). Prefer `mem20.com` in customer-facing copy. Every `/sites/` URL returns **403** anonymously — never publish or link one.
4. **House numbers, restated not re-measured:** TAM **$1.28B** / SAM **$282M** / SOM **$1.68M** / blended ACV **$14,000**.
5. **The benchmark exists and was re-run on a larger corpus.** `benchmarks/results/latest.md` — corpus `mem20-scale-corpus-v2`, **700 grounded / 1,300 simulated / 250 queries**, modes `keyword` + `semantic` only. Weakest rows: `keyword` **adversarial_hard 0.000 (n=40)** and **contradiction 0.050 (n=40)**; `semantic` scores 0.900 / 1.000 on the same classes. `hybrid` and `graph` are **unmeasured** — no rows ship. Leak 0.000 throughout. It ships only with its own "not comparable to competitor benchmarks" warning and the weak rows visible. **The retired 13-query / 14-fact figures must not be quoted** (`claim-ledger.md` §7 R17).

---

## Known drift this collateral must not propagate

| Where | Problem | Owner |
|---|---|---|
| GitHub repo `homepage` field | Points at a `/sites/` URL that returns **403**. Most-clicked link on the repo is a dead end. | Repo admin (one field) |
| `docs/index.html` (the live public page) | **CLOSED 2026-10-31.** Now prints 270 × 10 and 27 domains × 8, zero occurrences of the retired pair. | Closed |
| `docs/02-tools-reference.md` | Still prints the retired tool/domain pair. | Webpage Developer (P1) |
| `docs/05-complete-tools-reference.md` | Still prints the retired tool count in the header and the totals row. | Webpage Developer (P1) |
| `toolchest/inventory.json` | Regenerated `2026-10-29`; now `counts.mcp: 0` with `subsystem: 310`. It measures subsystems, not MCP tools — do not cite it for or against 270. | Closed (reclassified) |
| `docs/CNAME` | Names `mem20.jaysonai.online`, which has **no DNS record**. Pages therefore serves on `github.io` only. | Repo admin |

**The `docs/index.html` contradiction is closed** — the public page and the live server now agree at 270/27. The remaining P1 is the two in-tree reference docs above.

**Coordination note (H2).** The retired-infrastructure hostname cleanup in this directory is owned by branch `docs/ws1-retire-jaysonai-hostname`, which touches `docs/gtm/README.md`, `docs/gtm/claim-ledger.md` and `docs/gtm/mem20-campaign-plan.md`. This branch (`chore/gtm-claim-ledger-accuracy`) deliberately does **not** duplicate that string removal; it rebases on `main` at `f1672473` and carries only the numeric/claim corrections.
