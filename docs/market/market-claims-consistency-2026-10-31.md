# Market-claim consistency audit — 2026-10-31

**Action:** H16 — Market Research
**Repo:** `github.com/bythewayz66-glitch/mem20`
**Branch:** `chore/market-claims-consistency`
**Base (`main`):** `f1672473cd19d5926e1df0c80042259d3b4b17ca`

---

## 1. Verdict

| Measure | Result |
|---|---|
| Tracked text/doc files scanned | **6,989** |
| Files stating a market size or ACV | **45** |
| Distinct bound market-size / ACV statements | **174** |
| Statements matching the standing figures | **174** |
| Statements carrying a different figure | **0** |
| Docs presenting 120 accounts as a forecast | **0** |
| Docs stating a different TAM / SAM / SOM / ACV | **0** |

**No doc states a different TAM, SAM, SOM or blended ACV.** All 174 bound
statements across 45 files carry exactly one of the four standing values.
No doc presents the 120-account figure as a forecast — every one of the 47
occurrences is arithmetic (`120 x $14,000 = $1,680,000`), a definition
(`SOM accounts,120`), or an explicit prohibition
(`docs/gtm/claim-ledger.md:218` — "Do not present 120 accounts as a forecast.
It is the arithmetic consequence of three carried constants.").

Three **label-level** inconsistencies exist where the *figure* is right but the
*qualifier around it* is not unanimous. They are set out in §4. None of them
changes a number, so none is a value mismatch; all three are owner decisions
rather than things this audit may settle by re-derivation.

---

## 2. Method

Standing figures are the reference. They are **carried, not re-derived** — this
audit never recomputes a TAM, a SAM, a SOM or an ACV.

| Layer | Standing figure | Declared in |
|---|---|---|
| TAM | **$1.28B** | `docs/finance/inputs.json` → `house_numbers.tam_usd = 1280000000` |
| SAM | **$282M** | `docs/finance/inputs.json` → `house_numbers.sam_usd = 282000000` |
| SOM (ARR) | **$1.68M** | `docs/finance/inputs.json` → `house_numbers.som_arr_usd = 1680000` |
| Blended ACV | **$14,000** | `docs/finance/inputs.json` → `house_numbers.blended_acv_usd = 14000` |
| Accounts to realise SOM | **120** | `house_numbers.som_accounts = 120`, 120 x $14,000 = $1,680,000 exactly |

A dollar figure is counted as a **statement about a layer** only when it is
directly bound to that layer's token — `TAM $1.28B` or `$1.28B TAM` — across a
gap of connective words only. If the gap carries an arithmetic operator or a
digit (`SOM = 120 accounts x $14,000`), the figure is an operand in a formula,
not a restatement, and is skipped. Deltas, variances, residuals, sensitivity
outputs, tier prices, CAC, costs and gross profit are excluded by cue: they are
not claims about the size of the market.

Reproduce with:

```bash
python3 scripts/audit_market_claims.py .
```

Exit 0 = every statement matches, exit 1 = at least one does not, exit 2 = the
audit could not run. The checker is proven to fail on a bad figure: a
self-test fixture containing `TAM is $1.4B`, `Our SAM is $310M`,
`SOM: $2.1M` and `Blended ACV is $12,500` reports exactly those four
mismatches and returns exit 1.

---

## 3. Every market-size and ACV statement (174 of them)

The full per-statement inventory is reproducible, not transcribed. Run
`python3 scripts/audit_market_claims.py . -v` to print all 174 rows as
`file:line  LAYER  figure  STATUS`. Every row prints `MATCH`.

---

## 4. Label-level inconsistencies (figure correct, qualifier not unanimous)

These are reported, not fixed. Each is a labelling question, and resolving any
of them by inventing or re-deriving a number is exactly what this audit must
not do.

### 4.1 SOM horizon: "3-yr obtainable" vs "12-month obtainable"

The same **$1.68M** is published under two different horizons.

| Horizon | File:line | Text as written |
|---|---|---|
| 3-yr | `docs/finance/market_sizing.csv:6` | `SOM (3-yr obtainable)` |
| 3-yr | `published/sites/aca25e94-…/documents/mem20-finance-pricing-publish/market_sizing.csv:6` | `SOM (3-yr obtainable)` |
| 3-yr | `published/sites/aca25e94-…/documents/mem20-finance-pricing-publish/PUBLISH_REPORT.md:59` | `SOM (3-yr ARR)` |
| 3-yr | `published/sites/aca25e94-…/documents/mem20-finance-pricing-publish/unit_economics.csv:26` | `SOM accounts (3-yr obtainable)` |
| 3-yr | `published/sites/6c283fdf-…/documents/mem20-finance-report/README.md:39` | `SOM (3-yr ARR)` |
| 3-yr | `published/sites/6c283fdf-…/webpages/mem20-finance-report/index.html:294,623,642,664` | `SOM (3-yr ARR)` / `3-yr obtainable ARR` |
| **12-month** | `published/sites/54ed398d-…/webpages/mem20-market-research-v3/index.html:336` | `12-month obtainable, 120 accounts` |
| **12-month** | `published/sites/54ed398d-…/webpages/mem20-market-research-v3/index.html:980` | `$1.68M twelve-month obtainable target` |
| **12-month** | `published/sites/54ed398d-…/documents/mem20-market-research-v3/gabe-bundle/mem20-market-research-v3.html:336,980` | same two strings |
| **12-month** | `published/sites/dfe17c05-…/webpages/mem20-launch_v4/index.html:814` | `SOM · 12-month` |
| **12-month** | `published/sites/dfe17c05-…/webpages/mem20-launch_v4/index.html:958` | `SOM · 12-month obtainable` |

**Why it matters.** The canonical model states SOM as the *terminal* rung of a
three-year ramp (`docs/finance/model_output.json` → `ramp`: year 1 = 40
accounts, year 2 = 80, year 3 = 120; year-3 exit ARR $1,680,000). A figure
reached at the end of year 3 is not a 12-month obtainable. The 12-month label
therefore contradicts the model it quotes, while the 3-yr label matches it.
The two live marketing surfaces (`mem20-market-research-v3`, `mem20-launch_v4`)
carry the 12-month label; the finance artefacts carry 3-yr.

**Not resolved here:** choosing which label is canonical is an owner decision.
The recommendation is to align the two marketing surfaces to the model's 3-yr
horizon, because the model is the artefact that produces the number.

### 4.2 SAM account count: 20,100 vs 20,142 vs 20,143

$282M ÷ $14,000 = 20,142.86, so no integer account count reproduces the house
SAM exactly. Three counts circulate.

| Count | Status | File:line |
|---|---|---|
| **20,142** | canonical floor in the model | `docs/finance/README.md:91,106`; `docs/app/deck/slides/slide_05.html:37,53`; `published/sites/6c283fdf-…/webpages/mem20-finance-report/index.html:639`; `published/sites/aca25e94-…/…/PUBLISH_REPORT.md:58` |
| **20,100** | explicitly ruled the outlier | `docs/finance/README.md:103-108` — "20,100 is the outlier. The correct floor is 20,142" |
| **20,100** | still published as the count | `published/presentations/mem20_repo_v3/slide_07.html:39` (`~20,100 regulated accounts`); `published/sites/dfe17c05-…/webpages/mem20-launch_v4/index.html:841,957` (`~20,100 qualified accounts`); `published/sites/54ed398d-…/webpages/mem20-market-research-v3/index.html:855-856` (table row `SAM / 20,100`); `…/documents/mem20-market-research-v3/tam-sam-som-reconciliation.md:23` (`20,100 × 14,000 = $281,400,000`) |
| **20,143** | quoted as a division result | `docs/pricing/RECONCILIATION_NOTE.md:60` and `:126` — `$282M ÷ $14,000 ≈ 20,143` (house table states 20,142) |

**Why it matters.** `docs/finance/README.md` resolves the question explicitly and
in favour of 20,142. Three published marketing surfaces still carry 20,100, and
`mem20-market-research-v3` carries it while its own warning list at
`:877` says $282M implies 20,142.86 — the document contradicts itself one
section apart.

**Not resolved here:** the SAM dollar figure is unaffected ($282M everywhere),
so this is a count/label question only. The recommendation is that any published
surface quoting an account count uses 20,142, or quotes "~20,100" only with the
`approximately` qualifier that `mem20-market-research-v3:879` already prescribes.

### 4.3 Conditional single-rounding variant of TAM: $1.24B

| File:line | Text as written |
|---|---|
| `published/sites/54ed398d-…/webpages/mem20-market-research-v3/index.html:912` | "would shrink the TAM to about **$1.24B** on the same 19.72% share" |
| `published/sites/54ed398d-…/documents/mem20-market-research-v3/gabe-bundle/mem20-market-research-v3.html:912` | same |

Both instances are correctly framed as a *hypothetical* under a different
category base ("A diligence team using Mordor would shrink the TAM to about
$1.24B") and both sit inside a "what would make this document wrong" risk
section. This is **not** a competing house figure and does not breach the
standing number. It is flagged for one reason only: a reader who excerpts the
sentence without the conditional would publish a second TAM. No action is
recommended beyond keeping the conditional attached.

---

## 5. Explicitly NOT flagged, and why

These figures sit on the same lines as TAM/SAM/SOM tokens and are correct in
context. They are listed so a future reader does not mistake their absence from
§4 for an oversight.

| Figure | Where | Why it is not a market-size claim |
|---|---|---|
| $6.49B / $6.27B / $6.16B | 49 lines incl. `docs/finance/README.md:115`, `published/sites/dfe17c05-…/index.html:832` | Broad category base, always labelled context. `docs/finance/README.md:115`: "Any asset quoting $6.49B as mem20's TAM is out of family." |
| $1.29B, $1.73B | `mem20-market-research-v3/index.html:890`, `mem20-launch_v4/index.html:841` | Third-party forecast ranges (Mordor 2031) and a stated sensitivity floor, not the house TAM |
| −$600,000, −$594,000, $281.4M | `docs/pricing/RECONCILIATION_NOTE.md:127`, `docs/finance/README.md:103` | Disclosed SAM gap and total residual. Both are documented in the reconciliation ledger |
| −$8,000 / −$12,000, $1,279,992,000 / $281,988,000 | `docs/finance/README.md:90-91`, `market_sizing.csv:2` | The integer-floor builds, disclosed with their residuals; `inputs.json` forbids quoting them back as TAM or SAM |
| $1,280,006,000 | `docs/pricing/RECONCILIATION_NOTE.md:128` | The ceil build (91,429 x $14,000), disclosed as a rounding artefact |
| $1,166,400, $1,056,000 | `docs/finance/README.md:146`, `mem20-finance-report/README.md:29` | SOM-book gross profit and modelled cost — different metrics, not SOM ARR |
| $264,000, $538,000, $12,000–$74,000 | `docs/pricing/tier-sensitivity.md:161,213,216,252`, `:119-121` | Tier-sensitivity scenario outputs |
| $6,000 / $18,000 / $36,000 / $80,000 | `docs/finance/inputs.json`, `RECONCILIATION_NOTE.md` | Tier-level ACVs. The declared ladder 72/12/12/4 prices these and blends to $14,000 exactly |
| $8,000 / $16,800 | `docs/finance/model_output.json`, `mem20-finance-report/README.md:29` | Blended CAC, not ACV |

---

## 6. Scope limits

- **Which files.** Every tracked file with a doc-like extension (`.md`, `.html`,
  `.csv`, `.json`, `.txt`, `.yml`, `.yaml`, `.py`), 6,989 of them. Binary
  artefacts are out of scope. `published/` is in scope because those are the
  surfaces a reader actually opens.
- **What "matching" means.** Value equality against the standing figure, with
  the documented integer-floor builds accepted. It does **not** judge whether the
  house figures are *correct* as market estimates — that is a derivation
  question this audit is explicitly forbidden to answer.
- **Retired-name paths.** Four tracked files under
  `published/sites/54ed398d-…/documents/mem20-market-research-v3/gabe-bundle/`
  still carry `gabe` in their path. They are in scope and audited like any other
  file. The `chore(infra)` purge at `f1672473` deliberately excluded
  `published/sites/**` (its own commit message lists that exclusion), so these
  paths are expected to remain until the owning surface is re-published. Their
  *content* is clean: all four carry the standing figures.
- **What this audit did not do.** It did not invent a market number, did not
  re-derive the TAM, and did not edit any doc it audited. Findings in §4 are
  reported to their owning surfaces; fixing a marketing page is a Webpage
  Developer / Content Creator slice, and choosing a horizon or a count is an
  owner decision.

---

## 7. Decisions needed

1. **SOM horizon** — align the two marketing surfaces to `3-yr obtainable`, or
   restate the model's ramp so a 12-month figure is the one the model produces?
2. **SAM account count** — publish 20,142 everywhere, or keep 20,100 with the
   `approximately` qualifier? The finance README already argues for 20,142.
3. **$1.24B** — leave the conditional in place (recommended), or drop it from the
   public risk list to avoid a second TAM in circulation?

---

## 8. Owner decisions unchanged

The blended ACV remains **$14,000** (tier ladder reconciles to $0.00 delta) and
the TAM/SAM/SOM remain **$1.28B / $282M / $1.68M** as carried house figures.
This audit found no reason to reopen any of them, and did not.

---

**SOURCE:** standing figures read from `docs/finance/inputs.json`
(`house_numbers`), cross-checked against `docs/finance/market_sizing.csv`,
`docs/finance/model_output.json` and `docs/gtm/claim-ledger.md` §6 (H1–H5).
All file:line references above are at base
`f1672473cd19d5926e1df0c80042259d3b4b17ca`.

**DISCLAIMER:** As an AI Agent, I cannot provide legally protected, personalized
investment advice. This analysis is for informational purposes only and does not
constitute investment advice or recommendations. Consult a licensed financial
advisor before making investment decisions.
