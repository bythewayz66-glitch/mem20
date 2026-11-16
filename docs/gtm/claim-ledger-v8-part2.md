# mem20 — GTM Claim Ledger v8, Part 2: benchmark, house numbers, retired register

Companion to `docs/gtm/claim-ledger-v8-2026-11-16.md`. Split out only to keep each
file under the commit-size limit; the two files are one ledger and are versioned,
superseded and verified together.

**HEAD at capture:** `0224a64946a2c00313a9872515893157adcbc47e` (2026-11-16 06:55:07 +0000)
**Surface of record:** **487 tools / 129 domains** · **License of record:** **Apache-2.0** · **Version:** **4.0.0**
**Verification:** `python3 docs/gtm/verify/check_gtm_v8.py` and `python3 docs/gtm/verify/check_ledger.py` — both exit 0 = PASS.

---

## 5. The benchmark — every row the file ships

**Source:** `benchmarks/results/latest.json`. Corpus **`mem20-scale-corpus-v2`**: 700 grounded, 1,300 simulated, 250 queries. Reproduce: `python3 docs/gtm/verify/bench_rows.py`.

### 5.1 The full matrix — hit rate by mode × query class

| Mode | direct (n=60) | multi_hop (n=30) | adversarial (n=60) | adversarial_hard (n=40) | contradiction (n=40) | unanswerable (n=20) |
|---|---:|---:|---:|---:|---:|---:|
| `bm25` | 1.000 | 0.800 | 0.7667 | **0.025** | 0.050 | 0.000 |
| `vector` | 0.900 | 1.000 | 0.6667 | 0.750 | 1.000 | 0.000 |
| `hybrid` | 1.000 | 0.5333 | 0.1667 | 0.050 | 1.000 | 0.000 |
| `hybrid-rerank-off` | 1.000 | 1.000 | 0.650 | 0.625 | 1.000 | 0.000 |
| `graph` | — | **0.033** | — | — | — | — |
| `keyword` | 1.000 | 0.4667 | 0.1667 | **0.025** | 0.125 | 0.000 |
| `constant` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

`constant` is the control: it scores 0.000 everywhere, which is what a system that returns nothing scores. `graph` carries only `multi_hop` because only multi-hop probes carry an entity — a corpus property, not a skip.

### 5.2 The rerank pair

Both configurations are scored as standalone modes. On `adversarial_hard` rerank-off scores **0.625** against rerank-on **0.050**; on `multi_hop` rerank-off scores **1.000** against **0.5333**. `trust.rerank_off_note` says the contrast is in the recall table rather than a separate A/B. **Do not present reranking as a uniform win** — on this corpus rerank-on is the weaker of the two on the two hardest classes.

### 5.3 Modes declared but not scoreable

`recall`, `recall_at`, `entities` and `ledger` are declared surfaces with no row in the shipped file. They are **`unmeasured`**, not passing. Never present an unscored mode as a strength.

### 5.4 Trust block — measured this run

One command for every value below: `python3 -c "import json;print(json.load(open('benchmarks/results/latest.json'))['trust'])"`.

`contamination_rate` **0.0** · `contamination_violations` **0** · `stale_pointer_rate` **0.0** · `indexed_entries` **1400** · `graph_entities`/`graph_edges` **654/3601** · `degraded_queries` **0** · `queries_with_drift_diagnostic` **250** · `ledger_records` **700** · `all_reported_healthy` **true**.

### 5.5 The two notes the file ships with

1. *"Scores are NOT comparable to Mem0's LoCoMo/LongMemEval or Zep's DMR. Those run on different corpora with different metrics. These numbers describe this corpus only."*
2. *"NO LoCoMo RESULT IS CLAIMED. This harness has not been run against the LoCoMo originals, so no LoCoMo figure appears in this report and none may be quoted from it."*

**Never say:** any LoCoMo or LongMemEval figure for mem20; "matches Mem0"; "beats Zep"; "industry-leading retrieval".

---

## 6. House numbers

**Carried, not re-derived.** `docs/finance/inputs.json` → `house_numbers.provenance`: *"carried verbatim from the owner directive; NOT re-derived in this file."*

| Ref | Metric | Value | Status | Command (settles it) | Adversarial |
|---|---|---:|---|---|---|
| H1 | TAM | **$1.28B** | **VERIFIED** | `python3 -c "import json;print(json.load(open('docs/finance/inputs.json'))['house_numbers']['tam_usd'])"` | `n/a: market sizing` |
| H2 | SAM | **$282M** | **VERIFIED** | same, `sam_usd` | `n/a: market sizing` |
| H3 | SOM (ARR) | **$1.68M** | **VERIFIED** | same, `som_arr_usd` | `n/a: market sizing` |
| H4 | SOM account count | **120** | **VERIFIED** | same, `som_accounts` | `n/a: market sizing` |
| H5 | Blended ACV | **$14,000** | **VERIFIED** | same, `blended_acv_usd` | `n/a: pricing` |
| H6 | Tier ladder | Team $6,000 / Business $18,000 / Scale $36,000 / Enterprise $80,000 | **VERIFIED** | same, `tier_ladder` | `n/a: pricing` |
| H7 | Team-tier gross margin | **28.7%** | **VERIFIED** | `grep '^rung,mem20,Team' docs/market/price-positioning-2026-11-01.csv` | `n/a: pricing` |
| H8 | Team-tier CAC payback | **9.77 years** | **VERIFIED** | same | `n/a: pricing` |
| H9 | Blended gross margin / CAC payback | **69.4% / 1.73 years** | **VERIFIED** | `grep '^blend,mem20' docs/market/price-positioning-2026-11-01.csv` | `n/a: pricing` |

**H7/H8 are the commercial problem, and the sales motion is built around them.** At 28.7% gross margin and a 9.77-year CAC payback the Team tier is a land-and-expand entry point, not a business: it only works if it converts upward to Business (76.2% GM, 1.22-yr payback) or Scale (88.1% GM, 0.53-yr payback).

**Never say:** a TAM/SAM/SOM figure other than H1–H4; "we re-derived TAM"; a blended ACV other than $14,000.

---

## 7. Retired values — the sole register

These values were the surface of record at an earlier HEAD. They may appear **only** in this section, or on a line that names them as retired, superseded, historical or banned.

| Retired value | Was the surface of record at | Retired because | Superseded by |
|---|---|---|---|
| **270 tools** | v7, HEAD `2ea44922` (2026-11-01) | surface moved | **487 tools** |
| **27 domains** | v7, HEAD `2ea44922` (2026-11-01) | surface moved | **129 domains** |
| **268 tools / 26 domains** | v6 and earlier | surface moved | 487 / 129 |
| **258 tools** | pre-v6 | surface moved | 487 / 129 |
| **257 tools** | pre-v6 | surface moved | 487 / 129 |
| **311 tools / 39 domains** | finance model, pre-4.0 | surface moved | 487 / 129 |
| **MIT** (root license) | pre-`14e2ce0d` (before 2026-11-07) | **relicensed** | **Apache-2.0** |
| **3.1.0 / 3.1.2** (version) | v7 era | release moved | **4.0.0** |

**The three MIT sub-licenses are NOT retired.** `mem20-sdk-ruby/LICENSE`, `teamz/LICENSE` and `web/LICENSE` are MIT and correct — vendored components, not the root license.

---

## 8. Guardrails

| # | Rule |
|---|---|
| G1 | The surface is **487 tools across 129 domains**. Never 270, 27, 268, 26, 258, 257, 311 or 39 as current. |
| G2 | The license is **Apache-2.0**. Never "MIT" for the root repo. The three component sub-licenses may be named as MIT. |
| G3 | The version is **4.0.0**. Never 3.1.0 or 3.1.2 as current. |
| G4 | **No LoCoMo / LongMemEval figure** for mem20, ever. |
| G5 | The **adversarial 0.000-class rows stay visible** in any asset that quotes a retrieval number. |
| G6 | The promotion gate is **"narrowed, not closed"**. Never "airtight", "tamper-proof", "unfakeable", "provably secure". |
| G7 | Install is **source-only**. Never any `pip install mem20` form. |
| G8 | Never publish or link a `/sites/` or `/files/` URL as a destination — member-only, 403 anonymously. |
| G9 | House numbers are **carried, not re-derived**. Say so. |
| G10 | The **19 unwired tools** are named as unwired whenever the 487 count is broken down. |

---

## 9. Say / never say

| Claim | Say | Never say |
|---|---|---|
| License | Apache-2.0 — permissive, self-hostable, no lock-in, explicit patent grant | MIT, MIT core, MIT-licensed mem20 |
| Surface | 487 tools across 129 domains | 270 tools, 27 domains, ~487, over 450 |
| Unwired | 19 declared tools are not wired to the live surface | counting them as shipped |
| Benchmark | seven modes on our own 250-query corpus; the rows we lose are in the table | any LoCoMo / LongMemEval figure; matches Mem0; beats Zep |
| Adversarial | sparse 0.025, dense 0.750 — the split is the finding | one averaged adversarial score; 0.750 as the product score |
| Graph | graph scores 0.033 on multi-hop — our weakest mode | graph traversal as a strength |
| Promotion gate | evidence-based with an append-only audit trail; narrowed, not closed | tamper-proof, unfakeable, airtight, provably secure |
| Install | source-only: `git clone` + `pip install -r requirements.txt` | any `pip install mem20` form; available on PyPI |
| Public URL | `https://mem20.com/` | any `/sites/` or `/files/` URL as a destination |
| House numbers | carried from the owner directive, not re-derived | presenting them as measured this run |

---

## 10. Hand-off

**Next seat: VP of Sales.** Input: `docs/gtm/mem20-sales-motion-2026-11-16.md` + §6's tier ladder, specifically H7/H8.

**Then: Head of Marketing & Demand Generation**, to re-cut `docs/gtm/mem20-launch-copy*.md` against the main ledger's §1.2 (487/129), §3.4 (Apache-2.0) and this file's §8 (guardrails).
