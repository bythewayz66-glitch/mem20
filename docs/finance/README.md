# mem20 — Finance: reconciled model (canonical home)

**As of:** 2026-10-26 · **Canonical repo:** [bythewayz66-glitch/mem20](https://github.com/bythewayz66-glitch/mem20) (`main`, MIT)
**Prepared by:** Finance Assistant · **Deadline:** 2026-10-27T02:47Z

This directory is the repo-side home of the mem20 financial model. It supersedes the
finance artefacts under `published/sites/…/documents/mem20-finance-pricing-publish/`,
which remain in place as a **frozen snapshot dated 2026-10-14**.

---

## 1. House numbers — carried verbatim, never re-derived

| Figure | Value | Status in this model |
|---|---|---|
| Blended ACV | **$14,000** | derived from the tier ladder, asserts equal — **EXACT** |
| TAM | **$1.28B** | input, carried verbatim |
| SAM | **$282M** | input, carried verbatim |
| SOM | **$1.68M** | derived as 120 accounts × $14,000 — **EXACT** |

The house numbers are declared in [`inputs.json`](inputs.json) under `house_numbers`.
The model treats them as **inputs, not outputs**: `compute_model.py` recomputes each one
and exits non-zero rather than emit a drifted figure. It cannot silently agree with itself.

```bash
python3 docs/finance/compute_model.py --check   # verify only, writes nothing
python3 docs/finance/compute_model.py           # verify + regenerate all artefacts
```

## 2. What was checked, and what was found

Every ACV and market-size input was traced to its source and re-tested arithmetically.
Five findings; **two required a change, three are disclosed residuals**.

### 2.1 Blended ACV — no drift (held at $14,000)

The tier ladder is **72% / 12% / 12% / 4% on $6K / $18K / $36K / $80K**:

```
0.72 × 6,000  =  4,320
0.12 × 18,000 =  2,160
0.12 × 36,000 =  4,320
0.04 × 80,000 =  3,200
                ------
                 14,000   → house $14,000, delta $0.00
```

The shares sum to exactly 1.0. This reconciles to the house figure with **zero** residual.
Note this is *not* the 22/41/26/11 mix recorded in some earlier working notes — that mix
lands at $14,001 and belongs to a different ladder. The ladder actually committed in the
repo is the 72/12/12/4 above, and it is the one that reconciles exactly.

### 2.2 Tool surface — **drift found and fixed** (257/26 → 270/27)

The legacy model (`published/sites/…/mem20-finance-pricing-publish/compute_model.py`)
declares the repo state as `tools: 257, domains: 26`, and its corrections register
asserts *"C-10 Tools: 257-260 → 257"* and *"C-11 Domains: 26 → UNCHANGED"*.

That is stale against the live surface:

| Surface | Value |
|---|---|
| `verify_mcp.py` `MEM20_EXPECTED_TOOLS` default | **270** |
| `.github/workflows/mcp-verify.yml` pinned expectation | **270** |
| `CHANGELOG.md` [Unreleased] | **270 tools / 27 domains** |
| `docs/README.md` | **270 / 27** |
| domain modules under `mcp/tools/` | **27** |
| legacy finance model (superseded) | ~~257 / 26~~ |

**Fixed here:** `inputs.json → tool_surface` now declares **270 tools / 27 domains**, sourced
from the repo's own runtime verifier rather than a doc claim. The model also no longer lets
the tool count influence any revenue figure — it is carried as context only, so a future
count migration cannot silently move the market model. The P1 owner of the 257→270
migration elsewhere in the repo is the Webpage Developer.

### 2.3 Market layer arithmetic — no drift, residuals disclosed

| Layer | House value | Accounts (floor of value ÷ ACV) | Integer build | Residual |
|---|---|---|---|---|
| TAM | $1,280,000,000 | 91,428 | $1,279,992,000 | −$8,000 (−0.0006%) |
| SAM | $282,000,000 | 20,142 | $281,988,000 | −$12,000 (−0.0043%) |
| SOM | $1,680,000 | 120 | $1,680,000 | **$0 (exact)** |

TAM ÷ $14,000 = 91,428.57 accounts and SAM ÷ $14,000 = 20,142.86 accounts, so any integer
account count is by construction an approximation. **The house dollar figures are
authoritative; the account counts are derived and are not to be re-multiplied back into a
"corrected" TAM or SAM.** Ratios are quoted off the dollar figures:
SAM / TAM = **22.03%**, SOM / SAM = **0.596%**, SOM / TAM = **0.131%**.

### 2.4 Cross-asset drift in a downstream market doc — resolved

`published/sites/…/mem20-market-research-v3/tam-sam-som-reconciliation.md` builds the SAM
row on **20,100 accounts**, yielding $281.4M against the $282M house figure (−$600,000),
and then reports "SAM/TAM = 22.03% (20,100 / 91,429 = 21.98%)" — two ratios in one line.

**Resolution:** 20,100 is the outlier. The correct floor is **20,142** accounts, which
reproduces $282M to within $12,000 (0.004%); 20,100 does not reproduce it at all ($600,000
off, 25× the residual of the correct count). This model uses 20,142, and the 22.03% ratio is
computed from dollars (`$282M / $1.28B`), not from account counts. The v3 doc's own
instruction — *"do not add, subtract or re-derive SAM from the account count"* — is honoured.

### 2.5 Market-size inputs — no drift

TAM is the auditable agent-memory slice, **$1.28B**, not the broad $6.49B category figure
that some marketing copy quotes. Any asset quoting $6.49B as mem20's TAM is out of family.

## 3. Unit economics at the reconciled inputs

These lines are **repo-state dependent** and are recomputed from `inputs.json`, never hardcoded.

| Metric | Value | Basis |
|---|---|---|
| Hosting COGS | $1,880 /account/yr | declared |
| Support COGS | $2,400 /account/yr | 24 tickets × $100, 0 deflection channels |
| Total COGS | $4,280 /account/yr | hosting + support |
| Gross profit / account | $9,720 | $14,000 − $4,280 |
| Gross margin | **69.43%** | (stated as 69.4%) |
| Blended CAC | **$16,800** | $210/touch × 32 touches ÷ 0.40 close (0 inbound signals) |
| CAC payback | **1.73 yr** | CAC ÷ gross profit |
| LTV:CAC (full life) | 4.82× | 8.33-yr life at 12% churn |
| 3-yr LTV:CAC (Y1 cohort) | **2.01×** | below the 3.0× institutional hurdle |

**Disclosed, not smoothed:** the 3-year LTV:CAC of 2.01× sits below the 3.0× hurdle. That is
the honest reading of the captured repo state (0 stars, 0 forks, 0 releases, no package-index
entry, issue tracker and discussions both disabled), and it is reported as such rather than
adjusted by relaxing an input. The lever is distribution, not price.

## 4. SOM book

| Metric | Value |
|---|---|
| SOM accounts | 120 |
| SOM exit ARR | $1,680,000 |
| Acquisition cost to win the book | $2,016,000 (120 × $16,800) |
| Annual support cost | $288,000 (120 × $2,400) |
| Annual gross profit at SOM | $1,166,400 |

Ramp: **40 → 80 → 120** accounts, i.e. $560K → $1.12M → $1.68M exit ARR.

Note the acquisition cost of the full book ($2.02M) exceeds one year of gross profit
($1.17M) — payback is 1.73 years per account, so the book is funded from working capital
across the ramp, not from year-one margin. This is the single most important operating
constraint in the model.

## 5. Files

| Path | What |
|---|---|
| `inputs.json` | every declared assumption, including the house numbers and the 270/27 surface |
| `compute_model.py` | deterministic, offline, self-asserting model; generates everything below |
| `model_output.json` | full output: market, ACV, unit economics, SOM book, ramp, reconciliation |
| `unit_economics.csv` | cost stack, ACV tier ladder, acquisition and LTV metrics, ramp |
| `market_sizing.csv` | TAM → SAM → SOM bridge with account counts and residuals |
| `derivation_trace.csv` | figure → expression → computed value, for audit |
| `reconciliation_log.csv` | every input checked against its house number, with delta and status |

## 6. Change discipline

If a house number is to move, it moves in `inputs.json` **and** in the owner directive in the
same commit, and the assertion that pins it is updated in the same diff. A figure that moves
without an updated directive is drift; the model is designed to fail loudly on it rather than
publish a quietly different number.
