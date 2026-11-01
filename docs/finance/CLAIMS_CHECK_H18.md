# H18 — Financial-Claim Arithmetic Check

**Action:** H18 · **Owner:** Finance Assistant · **Re-run:** 2026-11-01
**Originally run:** 2026-10-31 · **Repo:** `github.com/bythewayz66-glitch/mem20`
**Base:** `main` @ `2ea4492209dfaae6afb22ca884132a0d1849bfcf`
**Roster row 18** of `docs/ops/owner-directive-2026-11-01.md` @ `06fa1220e964f84aabac78127fc18463dfa6798d`.

**Scope:** internal arithmetic consistency of the program's stated financial model as it appears in
**tracked** docs — TAM $1.28B, SAM $282M, SOM $1.68M, blended ACV $14,000 — plus any revenue, burn
or runway figure that could contradict another.

**What this is not.** Every figure below is an **arithmetic check on numbers the docs already
state**. Nothing here is a forecast, a projection, or a re-derivation of a house number. Where a
doc and arithmetic disagree, the doc is quoted and the arithmetic is shown; no house number is
proposed for change.

---

## 0. Surface-gate status — why this file was re-reviewed

The 2026-10-31 revision of this document reproduced the **retired domain count** verbatim inside its
M12/M13 evidence quotes. Those quotes were accurate quotations of other files, but a reader (and a
`grep`) cannot tell a quotation from an assertion, so the file itself read as carrying the stale
surface. That is now fixed at the source: this document quotes stale surfaces **by location and by
description**, never by reproducing the retired literals.

| Gate | Command | Result on this file |
|---|---|---|
| Retired-surface grep (row-18 acceptance) | `grep -cE '(258|260) tools|26[ -]domains' docs/finance/CLAIMS_CHECK_H18.md` | **0** |
| ACV-invariant gate | `python3 docs/pricing/audit_acv_consistency.py --no-surface` | **0 lines** attributed to this file |
| Tool-surface gate (full audit, gate on) | `python3 docs/pricing/audit_acv_consistency.py` | **0 lines** attributed to this file |
| Model self-check | `python3 docs/finance/compute_model.py --check` | **rc=0**, `270 tools / 27 domains` |

**Live surface of record:** **270 tools / 27 domains** (`python3 verify_mcp.py` → `TOOL_COUNT: 270`;
`ls mcp/tools/*.py | wc -l` → `27`). The retired tool counts and the retired domain count are
enumerated in exactly one place, `docs/gtm/claim-ledger.md` §7, and are **not** restated here.

**The financial model never read the tool count.** `docs/finance/model_output.json` and
`docs/finance/reconciliation_log.csv:11` both record that no revenue, market-size or unit-economics
figure in the model is derived from it, so the 270/27 migration moves **no** house number. That is
verified below, not assumed.

---

## 1. Arithmetic table — the four house numbers

Computed independently in this run (exact rational arithmetic for the ACV ladder; no value copied
from the model's own output).

| # | Relationship | Expression | Computed | Doc states | Delta | Verdict |
|---|---|---|---|---|---|---|
| A1 | Ladder blend | 0.72×6,000 + 0.12×18,000 + 0.12×36,000 + 0.04×80,000 | **$14,000.00** | $14,000 | $0.00 | **EXACT** |
| A2 | Tier shares sum | 0.72 + 0.12 + 0.12 + 0.04 | **1.0000** | 1.0 | 0 | **EXACT** |
| A3 | SOM identity | 120 accounts × $14,000 | **$1,680,000** | $1,680,000 | $0 | **EXACT** |
| A4 | SAM / TAM | 282,000,000 ÷ 1,280,000,000 | **22.0312%** | 22.03% | +0.0012 pp | **EXACT** (rounding) |
| A5 | SOM / SAM | 1,680,000 ÷ 282,000,000 | **0.5957%** | 0.596% | −0.0003 pp | **EXACT** (rounding) |
| A6 | SOM / TAM | 1,680,000 ÷ 1,280,000,000 | **0.1313%** | 0.131% | +0.0003 pp | **EXACT** (rounding) |
| A7 | TAM account floor | ⌊1,280,000,000 ÷ 14,000⌋ = 91,428 → 91,428 × 14,000 | **$1,279,992,000** | $1,280,000,000 | −$8,000 (−0.0006%) | **DISCLOSED** |
| A8 | SAM account floor | ⌊282,000,000 ÷ 14,000⌋ = 20,142 → 20,142 × 14,000 | **$281,988,000** | $282,000,000 | −$12,000 (−0.0043%) | **DISCLOSED** |
| A9 | Blended CAC | $210 × 32 touches ÷ 0.40 close | **$16,800** | $16,800 | $0 | **EXACT** |
| A10 | Support COGS | 24 tickets × $100 × (1 − 0) | **$2,400** | $2,400 | $0 | **EXACT** |
| A11 | Total COGS | 1,880 + 2,400 | **$4,280** | $4,280 | $0 | **EXACT** |
| A12 | Gross profit / account | 14,000 − 4,280 | **$9,720** | $9,720 | $0 | **EXACT** |
| A13 | Gross margin | 9,720 ÷ 14,000 | **69.4286%** | 69.43% | −0.0014 pp | **EXACT** (rounding) |
| A14 | CAC payback | 16,800 ÷ 9,720 | **1.7284 yr** | 1.73 yr | −0.0016 | **EXACT** (rounding) |
| A15 | Account life | 1 ÷ 0.12 | **8.3333 yr** | 8.33 yr | +0.0033 | **EXACT** (rounding) |
| A16 | LTV (full life) | 9,720 × 8.3333 | **$81,000** | $81,000 | $0 | **EXACT** |
| A17 | LTV:CAC (full life) | 81,000 ÷ 16,800 | **4.8214×** | 4.82× | +0.0014 | **EXACT** (rounding) |
| A18 | 3-yr GP multiplier | 1 + 1.15 + 1.15² | **3.4725×** | 3.4725× | 0 | **EXACT** |
| A19 | 3-yr LTV:CAC | 9,720 × 3.4725 ÷ 16,800 | **2.0091×** | 2.01× | −0.0009 | **EXACT** (rounding) |
| A20 | SOM support cost | 120 × 2,400 | **$288,000** | $288,000 | $0 | **EXACT** |
| A21 | SOM acquisition cost | 120 × 16,800 | **$2,016,000** | $2,016,000 | $0 | **EXACT** |
| A22 | SOM gross profit | 120 × 9,720 | **$1,166,400** | $1,166,400 | $0 | **EXACT** |
| A23 | Ramp exit ARR | 40/80/120 × 14,000 | **560K / 1.12M / 1.68M** | same | $0 | **EXACT** |
| A24 | SAM split | 45% + 55% of 282M; 9,064 + 11,078 accounts | **126.9M + 155.1M; 20,142** | same | $0 | **EXACT** |
| A25 | SOM / sales-led SAM | 1,680,000 ÷ 155,100,000 | **1.0832%** | 1.08% | +0.0032 pp | **EXACT** (rounding) |

**The four house numbers are internally consistent with each other.** SOM closes to zero against
120 accounts × $14,000 (A3); the ladder closes to zero against the blended figure (A1); the funnel
ratios are exact to the stated precision. `python3 docs/finance/compute_model.py --check` returns
**rc=0** on `main` @ `2ea44922`, reporting `270 tools / 27 domains`, `gross margin 69.43%`,
`CAC 16800.0`, `payback 1.73 yr`, `3-yr LTV:CAC 2.01x`, and `SOM arithmetic 120 accounts x 14,000
ACV = 1,680,000 (house 1,680,000: EXACT)`; regenerating the artefacts leaves the tree clean
(byte-idempotent).

**The mismatches below are not in the four house numbers. They are in the surrounding claims** —
account counts, a tier mix that does not reproduce, a mislabelled ratio, a mislabelled revenue
column, a cadence figure off by 4.3×, and one document that was itself polluting the repo's gates.

---

## 2. Mismatches — every one with file + line

### M1 — The repo's own blend audit fails on `main`, and the doc that describes it reports a clean pass with stale counts

| | |
|---|---|
| Doc states | `docs/pricing/RECONCILIATION_NOTE.md:13-18` — a four-row table reporting **2,011** files scanned, **44** figures found, **44** equal to the house blend, **0** disagreeing |
| Doc states | `docs/pricing/RECONCILIATION_NOTE.md:30` — "it exits non-zero the moment any figure drifts, so the invariant is now **enforceable in CI**" |
| Actual (this re-run) | `python3 docs/pricing/audit_acv_consistency.py --no-surface` → **EXIT 1**, `DRIFT DETECTED`, **2,072** files scanned, **115** figures found, **100** equal, **15** not equal |
| Actual (2026-10-31) | same command → 96 figures, 88 equal, 8 not equal |
| Verdict | **MISMATCH, and the gap is widening.** The note reports a four-row table of 2,011 / 44 / 44 / 0; the harness it describes now scans 2,072 files and finds 115 figures with 15 disagreements. The note's counts were already stale on 2026-10-31 (96/88/8) and have drifted further. The "enforceable in CI" claim remains **unsupported**: no workflow in `.github/workflows/` invokes `audit_acv_consistency.py` (`grep -rn audit_acv_consistency .github/workflows/` → no hits; only `finance-model-drift.yml` exists, and it runs `compute_model.py --check`). |

**Of the 15 flagged lines, 3 are this very document** — recorded as M14 below and **fixed** in this
revision. The remaining 12, verbatim from the run:

```
docs/finance/README.md:209                     $1,680,000
docs/finance/reconciliation_log.csv:4          $1,680,000
docs/finance/reconciliation_log.csv:5          $1,279,992,000
docs/finance/reconciliation_log.csv:6          $281,988,000
docs/finance/reconciliation_log.csv:8          $1,680,000
docs/market/market-claims-consistency-2026-10-31.md:23   $174
docs/market/market-claims-consistency-2026-10-31.md:68   $12,500
docs/market/market-claims-consistency-2026-10-31.md:73   $174
docs/pricing/RECONCILIATION_NOTE.md:15         $2,011
docs/pricing/TIER_SHIPPING_AUDIT.md:217        $4,280
docs/pricing/tier-sensitivity.md:271           $1,680,000
published/checkpoints/ledger.md:35             $340
```

**Honest reading of those 12:** they are **parser false positives, not blend drift.** `$2,011` is a
file count (`RECONCILIATION_NOTE.md:15`); `$340` is a fragment of commit SHA `d340a3a5…`
(`published/checkpoints/ledger.md:35`); `$174` is a count of statements, not a price
(`market-claims-consistency-2026-10-31.md:23` and `:73`); `$12,500` is a *quoted rejected* figure
(`:68`); `$4,280` is a COGS-per-account figure (`TIER_SHIPPING_AUDIT.md:217`); and the
`$1,680,000` / `$1,279,992,000` / `$281,988,000` hits are SOM and account-floor cells in CSV rows
and tables, not blended claims. So the **financial** content is sound — but the **doc's own counts
are wrong**, and the harness is red on `main`.

### M2 — The audit's failure count is stated as five; it is fifteen

| | |
|---|---|
| Doc states | `docs/pricing/tier-sensitivity.md:265-267` — "`audit_acv_consistency.py --no-surface` currently **exits 1 on five lines**" |
| Actual | **15** lines flagged this run (**12** once this document is excluded) |
| Verdict | **MISMATCH, worse than on 2026-10-31** (then: stated five, actual eight). The note's §9 enumerates five of the twelve and omits `docs/finance/README.md:209`, `docs/finance/reconciliation_log.csv:8`, `docs/pricing/tier-sensitivity.md:271` — the last of which is the note's own line — plus the four newer hits in `docs/market/market-claims-consistency-2026-10-31.md` and `docs/pricing/TIER_SHIPPING_AUDIT.md:217`. |

### M3 — The 22/41/26/11 mix is stated to land at $14,001; on the declared ladder it lands at $26,860

| | |
|---|---|
| Doc states | `docs/finance/README.md:59-60` — "this is *not* the 22/41/26/11 mix recorded in some earlier working notes — that mix **lands at $14,001** and belongs to a different ladder" |
| Arithmetic | 0.22×6,000 + 0.41×18,000 + 0.26×36,000 + 0.11×80,000 = **$26,860** (shares sum to 1.0) |
| Verdict | **MISMATCH (unchanged).** $14,001 is not reproducible from any ladder in the tree. The README correctly says it "belongs to a different ladder", but that ladder is not in the repo, so the $14,001 figure is unverifiable in-tree. Either name the ladder or drop the number. |

### M4 — TAM account count: 91,428 vs 91,429, with opposite-signed residuals

| | |
|---|---|
| Doc states | `docs/finance/market_sizing.csv:2` — TAM accounts **91,428** (floor; integer build $1,279,992,000, **−$8,000**, disclosed in the row's own note) |
| Doc states | `docs/pricing/RECONCILIATION_NOTE.md:61` and `:128` — "**91,429** accounts"; `:128` gives 91,429 × 14,000 = **$1,280,006,000 (+$6,000)** |
| Verdict | **MISMATCH (unchanged).** Two counts for the same quantity, and the residuals have **opposite signs** (−$8,000 vs +$6,000). Both are disclosed as rounding, but a reader cannot tell which count is canonical. Note `RECONCILIATION_NOTE.md:61` does not flag that the house table already states 91,428 — it does so for SAM on the next line, not for TAM. |

### M5 — SAM account count: three different values in tracked docs

| | |
|---|---|
| Doc states | `docs/finance/market_sizing.csv:3` — **20,142** (floor; integer build $281,988,000, −$12,000) |
| Doc states | `docs/pricing/RECONCILIATION_NOTE.md:60` and `:126` — "**20,143**" (build $282,002,000, +$2,000); `:126-127` also names **20,100** |
| Doc states | `published/sites/54ed398d-…/mem20-market-research-v3/tam-sam-som-reconciliation.md:23` — **20,100** (build $281,400,000, −$600,000) |
| Verdict | **MISMATCH (unchanged).** Three counts, three different residuals. `docs/finance/README.md:106` calls 20,100 "the outlier" and adopts 20,142 — but `RECONCILIATION_NOTE.md:60` still prints 20,143, and the v3 doc still prints 20,100. `RECONCILIATION_NOTE.md:124-133` now names this as "one open variance worth naming (not changed)", which discloses it without resolving it. |

### M6 — SOM is called "EXACT" while the repo's own sensitivity note says the declared mix has no integer realisation

| | |
|---|---|
| Doc states | `docs/finance/README.md:19` — SOM "derived as 120 accounts × $14,000 — **EXACT**"; `:92` — "**$0 (exact)**"; `:214-217` — "holds on **two** independent routes"; `:266-268` — "holds on **three** independent routes" |
| Doc states | `docs/app/deck/slides/slide_06.html:21` — "$1.68M is exact. That is the point."; `:49` — "variance $0 — EXACT" |
| Doc states | `docs/pricing/tier-sensitivity.md:83` — reachable mix 86/15/14/5 → **$1,690,000, +$10,000 (+0.60%)**; `:87` — "`120 × $14,000 = $1,680,000` and `86/15/14/5 of the same four tiers = $1,690,000` are two different worlds, and the repo currently states both **without acknowledging the gap**"; `:180` — "$1.68M is a **rounded blend at a nominal mix**, not `sum(tier price × integer accounts)`"; `:246` — "realisation is $1,690,000 at 86/15/14/5 (+0.60%), or $1,680,000 exactly at 86/18/10/6" |
| Arithmetic | 72% × 120 = 86.4, 12% × 120 = 14.4, 12% × 120 = 14.4, 4% × 120 = 4.8 — none integral. Brute force over all 302,621 integer mixes summing to 120 finds only **45** that hit $1,680,000 exactly (0.0149%). 86/15/14/5 → $1,690,000. 86/18/10/6 → $1,680,000. |
| Verdict | **MISMATCH (unchanged).** `$1.68M` is exact as `120 × $14,000` (A3) but is **not** the sum of the declared tier mix over whole accounts. The finance README and slide 06 assert exactness without the qualifier that `tier-sensitivity.md` §180 says must be disclosed. |

**Sub-claim also wrong:** "three independent routes" (`README.md:266-268`). The three named routes
are (i) 120 × $14,000, (ii) the ramp's terminal rung 120 × $14,000, and (iii) the term-by-term
ladder. Routes (i) and (ii) are **the same identity** — the ramp's terminal rung *is* 120 accounts —
and (iii) is a percentage-space identity that produces the blended figure, not $1,680,000. There
are **two** routes, not three, and `README.md:211` says "two" while `:266` says "three" in the same
document.

### M7 — `derivation_trace.csv` expression does not reproduce its own value

| | |
|---|---|
| Doc states | `docs/finance/derivation_trace.csv:16` — `SOM gross profit,1680000 x 0.6943,1166400` |
| Arithmetic | 1,680,000 × 0.6943 = **$1,166,424**, not $1,166,400 (delta **+$24**) |
| Correct expression | 1,680,000 × (9,720 ÷ 14,000) = 1,680,000 × 0.694285… = **$1,166,400** |
| Verdict | **MISMATCH (unchanged).** The trace's stated expression evaluates to a different number than the trace's stated value. The value is right; the expression is rounded too early. |

### M8 — `model_output.json` key name contradicts its value

| | |
|---|---|
| Doc states | `docs/finance/model_output.json:103` — `"cac_vs_3y_gross_profit": 1.73` |
| Arithmetic | Acquisition ÷ **1 year** of gross profit = 2,016,000 ÷ 1,166,400 = **1.7284** ✓ matches the value. Acquisition ÷ **3 years** of gross profit = 2,016,000 ÷ (1,166,400 × 3.4725) = **0.4977** |
| Verdict | **MISMATCH (unchanged).** The key says "3y"; the value is a 1-year ratio. `docs/finance/unit_economics.csv:26` labels the same 1.73 correctly as "SOM acquisition cost / annual gross profit", and `:13` labels it "CAC payback". |

### M9 — "SOM revenue" means ARR in two docs and recognised revenue in the model

| | |
|---|---|
| Doc states | `docs/pricing/RECONCILIATION_NOTE.md:72` — column header "**SOM revenue**" |
| Doc states | `docs/pricing/tier-sensitivity.md:80` and `:226` — column header "**SOM revenue**" |
| Doc states | `docs/finance/model_output.json:110,116,122` — `recognized_usd` **308,000 / 616,000 / 924,000** (0.55 recognition factor, `inputs.json:50`) |
| Arithmetic | 560,000 × 0.55 = 308,000; 1,120,000 × 0.55 = 616,000; 1,680,000 × 0.55 = 924,000 |
| Verdict | **MISMATCH (unchanged).** The same label "SOM revenue" denotes $1,680,000 (an ARR) in the two pricing docs and $924,000 (recognised) in the model's year 3. `grep -rn 'recognized\|recognised\|55%'` across `RECONCILIATION_NOTE.md`, `tier-sensitivity.md` and `docs/finance/README.md` returns **no hits**, so nothing reconciles the two; a reader comparing them sees a $756,000 gap with no explanation. |

### M10 — Sales one-pager cadence is off by 4.3×, and the AE coverage claim is off by 3.3×

| | |
|---|---|
| Doc states | `docs/gtm/mem20-sales-one-pager.md:66` — "At 120 accounts and a 4-quarter year, that is **30 net-new accounts per quarter** — roughly **2.3 per month**" |
| Arithmetic | 120 ÷ 4 = **30 per quarter** ✓. 120 ÷ 12 = **10 per month**, not 2.3. 2.3 is 120 ÷ 52 = **2.31 per week**. |
| Doc states | same line — "**Two enterprise AEs closing 1.5 accounts/month each covers the whole SOM**" |
| Arithmetic | 2 × 1.5 = 3 accounts/month = **36 per year = 30% of 120**, not the whole SOM |
| Verdict | **MISMATCH (two, same line).** "2.3 per month" should be 10 per month (or 2.3 per week); "covers the whole SOM" should be "covers 30% of the SOM". |

### M11 — GTM one-pager publishes a tier ladder that contradicts the declared ladder, and quotes the blend as a price

| | |
|---|---|
| Doc states | `docs/gtm/mem20-sales-one-pager.md:68` — "Packaging (proposal — no price list exists in the repo; these are GTM proposals, label them as such)"; `:73` — Supported tier priced at "**$14,000/yr** (the blended ACV anchor)" |
| Doc states | `docs/finance/inputs.json:38-43` — Team **$6,000** (72%) / Business **$18,000** (12%) / Scale **$36,000** (12%) / Enterprise **$80,000** (4%) |
| Doc states | `docs/pricing/RECONCILIATION_NOTE.md:86-88` — "**Never quote $14,000 to a customer.** It is a blend, not a price. The quotable objects are the four tier prices above; a rep who quotes the blend destroys both the entry point and the ceiling" |
| Verdict | **MISMATCH (unchanged).** Two different four-tier ladders are live in the repo, and the one-pager does exactly what the reconciliation note forbids — it lists the blend as a quotable tier price (`:73`). The one-pager does label the set "proposal — no price list exists in the repo" (`:68`), which mitigates but does not remove the contradiction with `inputs.json`. |

### M12 — **WITHDRAWN** — the `CHANGELOG.md` hit is a dated release entry, not live drift

| | |
|---|---|
| Cited on 2026-10-31 as | `CHANGELOG.md:117` — a "Note on house numbers" paragraph restating the retired surface beside the house figures |
| Re-check 2026-11-01 | Line 117 sits inside the **`## [3.0.0] — 2026-10-18 (consolidation baseline)`** section (heading at `CHANGELOG.md:52`). It is a historical release record of what 3.0.0 stated, not a current claim. `CHANGELOG.md:38-39` (the live `[Unreleased]` block) states **270 tools / 27 domains** and names the older pair as wrong in two ways. |
| Governing rule | `docs/gtm/claim-ledger.md` §7 **R14** — "Do not report historical changelog entries as live drift." |
| Verdict | **RETRACTED.** The 2026-10-31 revision of this document mis-scoped a dated changelog section as a live claim. Withdrawn per R14, not fixed — there is nothing to fix. |

### M13 — Six of eight daily reports state the retired surface on their house-numbers line without disclosure

| | |
|---|---|
| What | `published/daily-reports/*.md` each end with a "House numbers" line. Eight files carry the retired surface on it. Measurement: `for f in published/daily-reports/*.md; do grep -nE '(257|268) tools|26[ -]domains' "$f"; done` |
| Locations | `2026-10-24.md` lines **83, 84, 85, 102**; `2026-10-25.md` line **112**; `2026-10-26.md` lines **85, 175**; `2026-10-27.md` line **40**; `2026-10-28.md` line **39**; `2026-10-29.md` line **51**; `2026-10-30.md` line **52**; `2026-10-31.md` line **149** |
| Disclosed? | Only **two** of the eight: `2026-10-27.md:41` ("the legacy house number; the repo's own surface count at this date was the current one") and `2026-10-31.md:150` ("the legacy house number; the directly counted surface is the current one"). The other six print the retired pair with no qualifier. `2026-10-24.md:83-85` is different in kind — it records the retired pair as *observations of what the repo and the served page said that day*, which is a dated daily log doing its job; `:102` is the standing house-numbers line. |
| Verdict | **MISMATCH (narrowed).** Six standing house-numbers lines still assert a retired surface without the disclosure note that two sibling files already carry. The fix is one line of text per file — copy `2026-10-31.md:150`'s note — not a rewrite. These are dated logs, so the historical lines themselves are legitimate; it is the **undisclosed** ones that mislead. |

### M14 — **FIXED this run.** This document was itself a source of ACV-gate and surface-gate noise

| | |
|---|---|
| What | The 2026-10-31 revision reproduced the retired domain count inside its M12/M13 evidence quotes, and wrote the blend token adjacent to a bare account count and to the file-count number. The repo's own parser therefore read this document as making blend claims of **$120** and **$2,011**, and the surface grep read its quotations as assertions. |
| Measured | Before: `grep -cE '(258|260) tools|26[ -]domains'` → **4**; `audit_acv_consistency.py` → **3 lines** attributed to this file (`:30`, `:71`, `:89`). |
| Fix | Stale surfaces are now cited by **location and description only**; no retired literal is reproduced. The blend token is no longer placed immediately before a non-blend number. House figures are unchanged — only the surrounding wording moved. |
| After | `grep -c` → **0**; audit → **0 lines** attributed to this file. Verified in this run; see §5. |
| Verdict | **FIXED.** Recorded rather than silently deleted: a check's own output should not pollute the gates it runs. |

---

## 3. Checked and found consistent — no mismatch

Recorded so the next reviewer does not re-run these.

| Check | Result |
|---|---|
| **Burn rate / runway / EBIT / net loss / operating loss** | **No such figure exists anywhere in the tracked tree.** `git grep -iE 'EBIT\|runway\|burn rate\|monthly burn\|net loss'` returns only unrelated benchmark-corpus text (`mem20orcaz/corpus/…`) and code identifiers. There is therefore **no burn or runway claim that can contradict another** — the model states no burn and no runway at all. |
| **The superseded v2 unit-economics set** (CAC $2,210, 90% GM, 7% EBIT $117,600, LTV:CAC 17.1×, Bear $672K / Bull $3,024K) | **Absent from the tree.** `git grep` for `2,210`, `117,600`, `3,024,000` returns nothing. The live set is CAC $16,800 / GM 69.43% / 3-yr LTV:CAC 2.01×, and no doc states the old pair, so there is no live contradiction. |
| **$6.49B broad-category TAM** | Appears only as an explicitly **rejected** alternative (`docs/finance/README.md:114-115`, `docs/app/deck/slides/slide_05.html`, market-research-v3 §1). **Not present** in `docs/gtm/` or `published/README.md` / `long-form-v3`. No contradiction. |
| **SOM account count** | **120** everywhere it appears (`docs/finance/README.md:142`, `market_sizing.csv:6`, `unit_economics.csv:21`, `claim-ledger.md:209`, `sales-one-pager.md:64`). No competing count. |
| **Ramp figures** | 40/80/120 → $560K/$1.12M/$1.68M consistent across `README.md:148`, `unit_economics.csv:27-32`, `model_output.json:105-124`, `slide_06.html:30,37`. |
| **`compute_model.py --check`** | **rc=0** on `main` @ `2ea44922`; all house numbers reproduce; `git status --porcelain` clean after a full run (byte-idempotent). Now also prints `tool surface 270 tools / 27 domains`. |
| **`reconciliation_log.csv`** | **13 rows**, matching the CI floor in `.github/workflows/finance-model-drift.yml:46-47`. Append-only invariant holds. |
| **Tool-count migration moves no house number** | Confirmed by construction, not assumption: `model_output.json:254` and `reconciliation_log.csv:11` both record that no revenue, market-size or unit-economics figure reads the tool count; `reconciliation_log.csv:11` re-confirms the model against `270 / 27` with delta 0. |
| **270 / 27 is the live surface** | `python3 verify_mcp.py` → `TOOL_COUNT: 270`; `ls mcp/tools/*.py \| wc -l` → `27`; `compute_model.py --check` prints `270 tools / 27 domains`. Three independent reads agree. |

---

## 4. Summary

- **The four house numbers remain arithmetically consistent with each other.** TAM $1.28B, SAM
  $282M, SOM $1.68M and blended ACV $14,000 close exactly on every relationship the docs assert
  (A1–A6, A9–A25). SOM = 120 × $14,000 = $1,680,000 with zero residual. The 270/27 migration moves
  none of them.
- **This document now carries no retired surface.** `grep -cE '(258|260) tools|26[ -]domains'`
  returns **0**, and the repo's own blend audit attributes **0** lines to this file (was 3).
- **Twelve mismatches remain** (M1–M11, M13, M14; M12 withdrawn). The material ones are **M1** (the
  repo's own blend audit is red on `main` — 2,072 files / 115 figures / 15 disagreements — while the
  doc describing it reports a stale 2,011 / 44 / 44 / 0 and claims CI enforcement that does not
  exist), **M6** (SOM called "exact" while the repo's own sensitivity note says the declared mix has
  no integer realisation and the reachable mix is $1,690,000), **M9** ("SOM revenue" means two
  different numbers), **M10** (a cadence figure off by 4.3× and an AE-coverage claim off by 3.3×),
  and **M11** (two live tier ladders, one of which quotes the blend as a price that another doc
  forbids quoting).
- **One prior finding was wrong and is retracted.** M12 mis-scoped a dated `[3.0.0]` changelog entry
  as live drift; `claim-ledger.md` §7 **R14** already forbids exactly that reading.
- **No burn, runway, EBIT or net-loss figure exists in the tracked tree**, so no contradiction is
  possible on those axes. The superseded v2 unit-economics set is likewise absent.
- **No house number is proposed for change.** Every finding is either a labelling defect, a rounding
  disclosure that is stated in one doc and omitted in another, a count that differs between two
  docs, or a stale count in a doc describing a harness.

---

## 5. Re-run log — 2026-11-01

| Step | Command | Result |
|---|---|---|
| 1 | `git clone https://github.com/bythewayz66-glitch/mem20.git` | HEAD = `2ea4492209dfaae6afb22ca884132a0d1849bfcf` (`main`) |
| 2 | `grep -cE '(258|260) tools|26[ -]domains' docs/finance/CLAIMS_CHECK_H18.md` | **4** before this revision — the row-18 acceptance test **failed** |
| 3 | `python3 docs/finance/compute_model.py --check` | rc=0, `270 tools / 27 domains`, all house numbers EXACT |
| 4 | `python3 docs/pricing/audit_acv_consistency.py --no-surface` | EXIT 1; 2,072 files / 115 figures / 100 equal / 15 differ; **3** of those lines are this file |
| 5 | `python3 docs/pricing/audit_acv_consistency.py` (surface gate on) | 26 retired-surface hits repo-wide; **4** were in this file |
| 6 | `grep -rn 'audit_acv_consistency' .github/workflows/` | **no hits** — the "enforceable in CI" claim is unsupported |
| 7 | `for f in published/daily-reports/*.md; do grep -n …; done` | 8 files, 12 lines; 2 disclosed, 6 standing lines undisclosed |
| 8 | rewrite this document; re-run steps 2–5 | `grep -c` → **0**; audit → **0** lines attributed to this file |

**What changed in this revision.** Base SHA advanced `f1672473` → `2ea44922`; audit counts refreshed
96/88/8 → 2,072/115/100/15; M2's "five lines" → fifteen (twelve excluding this file); **M12
withdrawn** per `claim-ledger.md` §7 R14; M13 line numbers corrected and its disclosure split made
explicit (2 of 8 disclosed, not 0 of 8); **M14 added** and fixed; all retired surface literals
removed. The 25-row arithmetic table, M3–M11 and M1's core finding are unchanged and were re-verified
rather than re-asserted.

---

*Arithmetic checks on figures the docs already state. Not a forecast, not a projection, and not
investment advice.*
