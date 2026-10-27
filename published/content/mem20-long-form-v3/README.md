# mem20 long-form copy — v3 (canonical, 270 tools / 27 domains)

Single source of truth for every long-form / launch-copy asset. Supersedes the v1 and v2 sets,
which asserted **257 tools / 26 domains** and **268 tools / 26 domains** — both retired.

| File | What it is |
|---|---|
| `long-form-article.md` | Flagship deep-dive (~1,450 words) — auditability wedge |
| `launch-copy-pack.md` | Full launch copy pack (hero, subheads, PH/HN/X, ledger) |
| `show-hn-post.md` | Show HN post, publish-ready |
| `product-hunt-post.md` | Product Hunt tagline, description, maker comment |
| `social-threads.md` | X / LinkedIn / Reddit threads |
| `readme-install-block.md` | README + install block, source-only |
| `landing-page-copy-update.md` | Exact string replacements for the launch page |
| `campaign-plan.md` | Campaign plan + tracked-link convention |
| `claim-ledger.md` | Claim ledger V1–V8 / C1–C4 with provenance |
| `numbers-ledger.md` | **Every number used in copy, with its source** |
| `audit_report.csv` | Context-aware stale-reference audit (verdict per file) |

## Rules these files obey

1. **270 tools across 27 domains** is the only tool count. 257/26 and 268/26 are retired; they may appear only in a ledger row that labels them retired.
2. **Install is source-only.** PyPI `mem20`, `mem20-ai`, `mem20oreo` all return 404. Never present a bare `pip install mem20` as a working command.
3. **One public URL:** `https://bythewayz66-glitch.github.io/mem20/`. Internal static hosts return 403 to anonymous visitors and must not appear in shipped copy.
4. **Benchmarks are self-reported**, the adversarial hit rate is `0.000`, and no LoCoMo/LongMemEval result is claimed.
5. **Promotion is "evidence-based with an append-only audit trail"** — never tamper-proof, never unfakeable.
6. House numbers unchanged: TAM $1.28B / SAM $282M / SOM $1.68M, blended ACV $14,000.

See `numbers-ledger.md` for provenance and `audit_report.csv` for the per-file verdict.
