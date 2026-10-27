# mem20 long-form copy — v3 (canonical, 270 tools / 27 domains)

Single source of truth for every long-form and launch-copy asset. Supersedes the v1/v2 sets, which asserted 257 tools / 26 domains and then 268 tools / 26 domains — both retired.

| File | What it is |
|---|---|
| long-form-article.md | Flagship deep-dive (~1,450 words), auditability wedge |
| launch-copy-pack.md | Copy pack: positioning, install, numbers, guardrails |
| show-hn-post.md | Show HN post, publish-ready |
| product-hunt-post.md | Product Hunt tagline, description, maker comment |
| social-threads.md | X single plus 6-post thread, LinkedIn, three Reddit variants |
| readme-install-block.md | README header and install block, source-only |
| landing-page-copy-update.md | Exact string replacements for the launch page |
| campaign-plan.md | Campaign sequence and tracked-link convention |
| claim-ledger.md | Verified facts and copy-claim dispositions |
| numbers-ledger.md | Every number used in copy, with its source |
| audit_report.csv | Context-aware stale-reference audit, verdict per file |

## Rules these files obey

1. **270 tools across 27 domains** is the only tool count. 257/26 and 268/26 may appear only in a row that labels them retired.
2. **Install is source-only.** PyPI returns 404 for mem20, mem20-ai and mem20oreo. Never present a bare registry install as working.
3. **One public URL:** the GitHub Pages site. Internal static hosts return 403 to anonymous visitors and must not appear in shipped copy.
4. **Benchmarks are self-reported**, the adversarial hit rate is 0.000, and no LoCoMo or LongMemEval result is claimed.
5. **Promotion is evidence-based with an append-only audit trail** — never tamper-proof, never unfakeable.
6. House numbers unchanged: TAM $1.28B / SAM $282M / SOM $1.68M, blended ACV $14,000.

### Audit status

12/12 assets PASS the context-aware stale-reference scan with zero assertive stale values. Negative control: 5/5 pre-correction files (README, docs/index.html, Show HN, install block, GTM launch copy) are correctly flagged by the same scanner, so the PASS is discriminating rather than vacuous.
