# docs/gtm — GTM collateral (v3, current)

**Owner:** mem20 GTM Team Lead · **Captured:** 2026-10-26 · **Repo HEAD:** `7c0b3e8` · **Version:** 3.0.0
**Canonical repo:** https://github.com/bythewayz66-glitch/mem20
**Canonical public URL:** https://bythewayz66-glitch.github.io/mem20/

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
3. **The only public web URL is `https://bythewayz66-glitch.github.io/mem20/`** (HTTP 200, byte-identical to `docs/index.html`). Every `/sites/` URL returns **403** anonymously — never publish or link one.
4. **House numbers, restated not re-measured:** TAM **$1.28B** / SAM **$282M** / SOM **$1.68M** / blended ACV **$14,000**.
5. **The benchmark exists and is small.** `benchmarks/results/latest.md`: direct 1.000, multi-hop 0.800, adversarial **0.000**, leak 0.000, 13 queries. It ships only with its own "not comparable to competitor benchmarks" warning and the 0.000 row visible.

---

## Known drift this collateral must not propagate

| Where | Problem | Owner |
|---|---|---|
| GitHub repo `homepage` field | Points at a `/sites/` URL that returns **403**. Most-clicked link on the repo is a dead end. | Repo admin (one field) |
| `docs/index.html` (the live public page) | Still says **268 / 26 domains** (4× `268`, 4× `26 domains`, 0× `270`). The public page contradicts the live server. | Webpage Developer (P1) |
| `docs/02-tools-reference.md` | Says **268 / 26**. | Webpage Developer (P1) |
| `toolchest/inventory.json` | `counts.mcp: 258`, `generated_at: 2026-10-07` — stale. | Webpage Developer (P1) |
| `docs/CNAME` | **Resolved.** Names `mem20.com`, which resolves and returns 200. The old legacy-zone hostname is retired — do not cite it. | Closed (2026-10-31) |

Until the `docs/index.html` fix lands, **campaign copy says 270/27 and the public page says 268/26.** That contradiction is one click from any HN commenter. It is a P1, not a documentation nit.
