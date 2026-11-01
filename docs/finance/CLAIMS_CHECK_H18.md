# H18 — Financial-Claim Arithmetic Check

**Action:** H18 · **Owner:** Finance Assistant · **Date:** 2026-10-31
**Repo:** `github.com/bythewayz66-glitch/mem20`
**Base:** `main` @ `f1672473cd19d5926e1df0c80042259d3b4b17ca`
(the action named `27c1e5fb78def1d34b9b8f572a66f1424b1b350e`; that commit is an **ancestor** of the
current head — `main` has advanced 2 commits since, both in `docs/ops/` and `.github/`, neither
touching `docs/finance/` or `docs/pricing/`. This check was run against the live head.)

**Scope:** internal arithmetic consistency of the program's stated financial model as it appears in
**tracked** docs — TAM $1.28B, SAM $282M, SOM $1.68M, blended ACV $14,000 — plus any revenue, burn
or runway figure that could contradict another.

**What this is not.** Every figure below is an **arithmetic check on numbers the docs already
state**. Nothing here is a forecast, a projection, or a re-derivation of a house number. Where a
doc and arithmetic disagree, the doc is quoted and the arithmetic is shown; no house number is
proposed for change.

---

## 1. Arithmetic table — the four house numbers

Computed independently in this run (exact rational arithmetic for the ACV ladder; no value copied
from the model's own output).

| # | Relationship | Expression | Computed | Doc states | Delta | Verdict |
|---|---|---|---|---|---|---|
| A1 | ACV ladder blend | 0.72×6,000 + 0.12×18,000 + 0.12×36,000 + 0.04×80,000 | **$14,000.00** | $14,000 | $0.00 | **EXACT** |
| A2 | Tier shares sum | 0.72 + 0.12 + 0.12 + 0.04 | **1.0000** | 1.0 | 0 | **EXACT** |
| A3 | SOM = accounts × ACV | 120 × $14,000 | **$1,680,000** | $1,680,000 | $0 | **EXACT** |
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
120 accounts × $14,000; the ACV ladder closes to zero against $14,000; the funnel ratios are exact
to the stated precision. `python3 docs/finance/compute_model.py --check` returns rc=0 and
regenerating the artefacts leaves the tree clean (byte-idempotent).

**The mismatches below are not in the four house numbers. They are in the surrounding claims** —
account counts, a mix that does not reproduce, a mislabelled ratio, a mislabelled revenue column,
and a cadence figure that is off by 4.3×.

---

## 2. Mismatches — every one with file + line

### M1 — The repo's own ACV audit fails on `main`, and the doc that describes it says it passes

| | |
|---|---|
| Doc states | `docs/pricing/RECONCILIATION_NOTE.md:15-18` — "Files scanned for ACV claims **2,011**", "ACV figures found **44**", "Figures equal to $14,000 **44**", "Figures disagreeing with $14,000 **0**" |
| Doc states | `docs/pricing/RECONCILIATION_NOTE.md:30` — "it exits non-zero the moment any figure drifts, so the invariant is now **enforceable in CI**" |
| Arithmetic / actual | `python3 docs/pricing/audit_acv_consistency.py --no-surface` → **EXIT=1**, `DRIFT DETECTED`, **96** figures found, **88** equal, **8** not equal |
| Verdict | **MISMATCH.** The note reports 44/44/0; the harness it describes reports 96/88/8 and fails. The "enforceable in CI" claim is also unsupported: no workflow in `.github/workflows/` invokes `audit_acv_consistency.py` (only `finance-model-drift.yml` exists, and it runs `compute_model.py`). |

The 8 flagged lines, verbatim from the run:

```
docs/finance/README.md:209                    $1,680,000
docs/finance/reconciliation_log.csv:4         $1,680,000
docs/finance/reconciliation_log.csv:5         $1,279,992,000
docs/finance/reconciliation_log.csv:6         $281,988,000
docs/finance/reconciliation_log.csv:8         $1,680,000
docs/pricing/RECONCILIATION_NOTE.md:15        $2,011
docs/pricing/tier-sensitivity.md:271          $1,680,000
published/checkpoints/ledger.md:35            $340
```

**Honest reading of those 8:** they are **parser false positives, not ACV drift.** `$2,011` is a
file count (`RECONCILIATION_NOTE.md:15`); `$340` is a fragment of commit SHA `d340a3a5…`
(`published/checkpoints/ledger.md:35`); the `$1,680,000` / `$1,279,992,000` / `$281,988,000` hits
are SOM and account-floor cells in CSV rows and tables, not blended-ACV claims. So the *financial*
content is sound — but the **doc's own count (44/44/0) is wrong**, and the harness is red on `main`.

### M2 — The audit's failure count is stated as five; it is eight

| | |
|---|---|
| Doc states | `docs/pricing/tier-sensitivity.md:265-267` — "`audit_acv_consistency.py --no-surface` currently **exits 1 on five lines**" |
| Actual | **8** lines flagged (list above) |
| Verdict | **MISMATCH.** The note enumerates five of the eight and omits `docs/finance/README.md:209`, `docs/finance/reconciliation_log.csv:8`, and `docs/pricing/tier-sensitivity.md:271` — the last of which is the note's own line. |

### M3 — The 22/41/26/11 mix is stated to land at $14,001; on the declared ladder it lands at $26,860

| | |
|---|---|
| Doc states | `docs/finance/README.md:59-60` — "this is *not* the 22/41/26/11 mix recorded in some earlier working notes — that mix **lands at $14,001** and belongs to a different ladder" |
| Arithmetic | 0.22×6,000 + 0.41×18,000 + 0.26×36,000 + 0.11×80,000 = **$26,860** (shares sum to 1.0) |
| Verdict | **MISMATCH.** $14,001 is not reproducible from any ladder in the tree. The README correctly says it "belongs to a different ladder", but that ladder is not in the repo, so the $14,001 figure is unverifiable in-tree. Either name the ladder or drop the number. |

### M4 — TAM account count: 91,428 vs 91,429, with opposite-signed residuals

| | |
|---|---|
| Doc states | `docs/finance/market_sizing.csv:2` — TAM accounts **91,428** (floor; rebuild $1,279,992,000, **−$8,000**) |
| Doc states | `docs/pricing/RECONCILIATION_NOTE.md:61` and `:128` — "**91,429** accounts"; `:128` gives 91,429 × 14,000 = **$1,280,006,000 (+$6,000)** |
| Verdict | **MISMATCH.** Two counts for the same quantity, and the residuals have **opposite signs** (−$8,000 vs +$6,000). Both are disclosed as rounding, but a reader cannot tell which count is canonical. |

### M5 — SAM account count: three different values in tracked docs

| | |
|---|---|
| Doc states | `docs/finance/market_sizing.csv:3` — **20,142** (floor; rebuild $281,988,000, −$12,000) |
| Doc states | `docs/pricing/RECONCILIATION_NOTE.md:60` and `:126` — "**20,143**" (rebuild $282,002,000, +$2,000) |
| Doc states | `published/sites/54ed398d-…/mem20-market-research-v3/tam-sam-som-reconciliation.md:23` — **20,100** (rebuild $281,400,000, −$600,000) |
| Verdict | **MISMATCH.** Three counts, three different residuals. `docs/finance/README.md:106` calls 20,100 "the outlier" and adopts 20,142 — but `RECONCILIATION_NOTE.md:60` still prints 20,143 in the same repo, and the v3 doc still prints 20,100. |

### M6 — SOM is called "EXACT" while the repo's own sensitivity note says the declared mix has no integer realisation

| | |
|---|---|
| Doc states | `docs/finance/README.md:19` — SOM "derived as 120 accounts × $14,000 — **EXACT**"; `:92` — "**$0 (exact)**"; `:214-217` — "holds on **two** independent routes"; `:266-268` — "holds on **three** independent routes" |
| Doc states | `docs/app/deck/slides/slide_06.html:21` — "$1.68M is exact. That is the point."; `:49` — "variance $0 — EXACT" |
| Doc states | `docs/pricing/tier-sensitivity.md:83-84` — reachable mix 86/15/14/5 → **$1,690,000, +$10,000 (+0.60%)**; `:87-90` — "`120 × $14,000 = $1,680,000` and `86/15/14/5 of the same four tiers = $1,690,000` are two different worlds, and the repo currently states both **without acknowledging the gap**"; `:107-108` — 72/12/12/4 "has **no integer realisation** at this logo count"; `:180` — "$1.68M is a **rounded blend at a nominal mix**, not `sum(tier price × integer accounts)`" |
| Arithmetic | 72% × 120 = 86.4, 12% × 120 = 14.4, 12% × 120 = 14.4, 4% × 120 = 4.8 — none integral. Brute force over all 302,621 integer mixes summing to 120: only **45** hit $1,680,000 exactly (0.0149%). 86/15/14/5 → $1,690,000. 86/18/10/6 → $1,680,000. |
| Verdict | **MISMATCH.** `$1.68M` is exact as `120 × $14,000` (A3) but is **not** the sum of the declared tier mix over whole accounts. The finance README and slide 06 assert exactness without the qualifier that `tier-sensitivity.md` says must be disclosed. |

**Sub-claim also wrong:** "three independent routes" (`README.md:266-268`). The three named routes
are (i) 120 × $14,000, (ii) the ramp's terminal rung 120 × $14,000, and (iii) the term-by-term ACV
ladder. Routes (i) and (ii) are **the same identity** — the ramp's terminal rung *is* 120 accounts —
and (iii) is a percentage-space identity that produces $14,000, not $1,680,000. There are **two**
routes, not three, and `README.md:214` says "two" while `:266` says "three" in the same document.

### M7 — `derivation_trace.csv` expression does not reproduce its own value

| | |
|---|---|
| Doc states | `docs/finance/derivation_trace.csv:16` — `SOM gross profit,1680000 x 0.6943,1166400` |
| Arithmetic | 1,680,000 × 0.6943 = **$1,166,424**, not $1,166,400 (delta **+$24**) |
| Correct expression | 1,680,000 × (9,720 ÷ 14,000) = 1,680,000 × 0.694285… = **$1,166,400** |
| Verdict | **MISMATCH.** The trace's stated expression evaluates to a different number than the trace's stated value. The value is right; the expression is rounded too early. |

### M8 — `model_output.json` key name contradicts its value

| | |
|---|---|
| Doc states | `docs/finance/model_output.json:103` — `"cac_vs_3y_gross_profit": 1.73` |
| Arithmetic | Acquisition ÷ **1 year** of gross profit = 2,016,000 ÷ 1,166,400 = **1.7284** ✓ matches the value. Acquisition ÷ **3 years** of gross profit = 2,016,000 ÷ (1,166,400 × 3.4725) = **0.4977** |
| Verdict | **MISMATCH.** The key says "3y"; the value is a 1-year ratio. `docs/finance/unit_economics.csv:26` labels the same 1.73 correctly as "SOM acquisition cost / annual gross profit". |

### M9 — "SOM revenue" means ARR in two docs and recognised revenue in the model

| | |
|---|---|
| Doc states | `docs/pricing/RECONCILIATION_NOTE.md:72-78` — column header "**SOM revenue**", base row **$1,680,000** |
| Doc states | `docs/pricing/tier-sensitivity.md:226-232` — column header "**SOM revenue**", base row **$1,680,000** |
| Doc states | `docs/finance/model_output.json:110,116,122` — `recognized_usd` **308,000 / 616,000 / 924,000** (55% recognition factor, `inputs.json:50`) |
| Arithmetic | 560,000 × 0.55 = 308,000; 1,120,000 × 0.55 = 616,000; 1,680,000 × 0.55 = 924,000 |
| Verdict | **MISMATCH.** The same label "SOM revenue" denotes $1,680,000 (an ARR) in the two pricing docs and $924,000 (recognised) in the model's year 3. No doc reconciles the two, and a reader comparing them sees a $756,000 gap with no explanation. |

### M10 — Sales one-pager cadence is off by 4.3×, and the AE coverage claim is off by 3.3×

| | |
|---|---|
| Doc states | `docs/gtm/mem20-sales-one-pager.md:66` — "At 120 accounts and a 4-quarter year, that is **30 net-new accounts per quarter** — roughly **2.3 per month**" |
| Arithmetic | 120 ÷ 4 = **30 per quarter** ✓. 120 ÷ 12 = **10 per month**, not 2.3. 2.3 is 120 ÷ 52 = **2.31 per week**. |
| Doc states | same line — "**Two enterprise AEs closing 1.5 accounts/month each covers the whole SOM**" |
| Arithmetic | 2 × 1.5 = 3 accounts/month = **36 per year = 30% of 120**, not the whole SOM |
| Verdict | **MISMATCH (two, same line).** "2.3 per month" should be 10 per month (or 2.3 per week); "covers the whole SOM" should be "covers 30% of the SOM". |

### M11 — GTM one-pager publishes a tier ladder that contradicts the declared ladder, and quotes $14,000 as a price

| | |
|---|---|
| Doc states | `docs/gtm/mem20-sales-one-pager.md:72-75` — Free **$0** / Supported **$14,000/yr** / Compliance pack **$28,000–$42,000/yr** / Platform **$56,000+/yr** |
| Doc states | `docs/finance/inputs.json:38-43` — Team **$6,000** (72%) / Business **$18,000** (12%) / Scale **$36,000** (12%) / Enterprise **$80,000** (4%) |
| Doc states | `docs/pricing/RECONCILIATION_NOTE.md:86-88` — "**Never quote $14,000 to a customer.** It is a blend, not a price. The quotable objects are the four tier prices above" |
| Verdict | **MISMATCH.** Two different four-tier ladders are live in the repo, and the one-pager does exactly what the reconciliation note forbids — it lists $14,000 as a quotable price (`:73`). The one-pager does label the set "proposal — no price list exists in the repo" (`:68`), which mitigates but does not remove the contradiction with `inputs.json`. |

### M12 — `CHANGELOG.md` states a retired tool surface in the same sentence as the house numbers

| | |
|---|---|
| Doc states | `CHANGELOG.md:117` — "268 tools / 26 domains, TAM $1.28B / SAM $282M / SOM $1.68M, blended ACV $14,000" |
| Doc states | `docs/gtm/README.md:24` — "**270 tools across 27 domains.** … Retired: 257, 258, **268**"; `docs/gtm/claim-ledger.md:229` — "**R2** `268 tools / 26 domains` — **RETIRED**" |
| Verdict | **MISMATCH (non-financial, adjacent).** The financial figures in that sentence are correct; the tool count beside them is a value the repo's own claim ledger marks retired. Flagged because it sits in the same "house numbers" statement. |

### M13 — Eight daily reports state a retired tool surface beside the house numbers

| | |
|---|---|
| Doc states | `published/daily-reports/2026-10-24.md:102`, `2026-10-25.md:112`, `2026-10-26.md:175`, `2026-10-27.md:40`, `2026-10-28.md:39`, `2026-10-29.md:51`, `2026-10-30.md:52`, `2026-10-31.md:149` — "**257 tools** across 26 domains · TAM $1.28B / SAM $282M / SOM $1.68M · blended ACV $14,000" |
| Doc states | `docs/gtm/claim-ledger.md:228` — "**R1** `257 tools / 26 domains` — **RETIRED**" |
| Verdict | **MISMATCH (non-financial, adjacent).** Same pattern as M12: correct financial figures, retired tool count in the same standing line, across 8 files. |

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
| **`compute_model.py --check`** | rc=0; all house numbers reproduce; regeneration is byte-idempotent (`git status` clean after a full run). |
| **`reconciliation_log.csv`** | 13 rows, matching the CI floor in `finance-model-drift.yml:46`. Append-only invariant holds. |

---

## 4. Summary

- **The four house numbers are arithmetically consistent with each other.** TAM $1.28B, SAM $282M,
  SOM $1.68M and blended ACV $14,000 close exactly on every relationship the docs assert (A1–A6,
  A9–A25). SOM = 120 × $14,000 = $1,680,000 with zero residual.
- **13 mismatches** are reported above, each with file + line. The material ones are **M1** (the
  repo's own ACV audit is red on `main` while the doc describing it reports a clean pass), **M6**
  (SOM called "exact" while the repo's own sensitivity note says the declared mix has no integer
  realisation and the reachable mix is $1,690,000), **M9** ("SOM revenue" means two different
  numbers), **M10** (a cadence figure off by 4.3× and an AE-coverage claim off by 3.3×), and
  **M11** (two live tier ladders, one of which quotes $14,000 as a price that another doc forbids
  quoting).
- **No burn, runway, EBIT or net-loss figure exists in the tracked tree**, so no contradiction is
  possible on those axes. The superseded v2 unit-economics set is likewise absent.
- **No house number is proposed for change.** Every finding is either a labelling defect, a
  rounding disclosure that is stated in one doc and omitted in another, or a count that differs
  between two docs. The arithmetic itself holds.

---

*Arithmetic checks on figures the docs already state. Not a forecast, not a projection, and not
investment advice.*
