# Price positioning — what the category's published prices say about a $14,000 blended ACV

**Lane:** H16 — Market Research (pricing and positioning)
**Repo:** `github.com/bythewayz66-glitch/mem20`
**Baseline:** `main` at `d99ab5d8e9c5c45a1fb3d02d3b65b2f9a96b5110`
**Prices read:** 2026-11-01, vendors' own pricing pages
**Companions:** `price-positioning-2026-11-01.csv`, `scripts/verify_price_ladder.py`
**Does not supersede:** `docs/market/competitive-matrix-2026-11-01.md` (that file owns the feature matrix and the per-player price refresh). This file addresses the one question that matrix records but does not test: **whether the price ladder holds up against what buyers can actually buy elsewhere.**

---

## 1. Verdict

The house numbers are not in question here. They are carried:

| Layer | Carried figure | Declared in |
|---|---|---|
| TAM | **$1.28B** | `docs/finance/inputs.json` → `house_numbers.tam_usd` |
| SAM | **$282M** | `house_numbers.sam_usd` |
| SOM (ARR) | **$1.68M** | `house_numbers.som_arr_usd` |
| Blended ACV | **$14,000** | `house_numbers.blended_acv_usd` |
| Accounts to realise SOM | **120** | `house_numbers.som_accounts` |

What this analysis adds is a stress test of the **price** against the **supply side**, and it
returns four findings that do not appear in the competitive matrix:

| # | Finding | Consequence |
|---|---|---|
| **F1** | The category's highest **published self-serve price** is **$4,500 a year** (Zep Flex Plus, $375/mo). The blended ACV is **3.11× above that ceiling**; even the cheapest mem20 rung (Team, $6,000) is **1.33× above it** | No buyer arriving through a self-serve, card-and-checkout motion pays this. The price forces a governance buyer |
| **F2** | The declared **72% Team share is the exact ceiling** that preserves $14,000 — algebraically, not approximately. A 1-point shift down-market costs **$120 of ACV** and **$14,400 of SOM** | The model has **zero** mix headroom. There is no room for a single mispriced deal |
| **F3** | At the model's **own absolute COGS** ($4,280/account), the Team tier runs a **28.7% gross margin** and a **9.77-year CAC payback**, against a blended **69.43%** and **1.73 years** | **72% of the book is priced at a 9.77-year payback** while the blended line advertises 1.73. The blended line is a mix artefact, not an account-level truth |
| **F4** | The model labels a **$126.9M / 9,064-account** slice "self-serve, PLG motion" at **$14,000.44 per account** | A slice priced at **3.11× the category's self-serve ceiling** is not self-serve. Either the label or the price is wrong |

**The single sentence:** mem20's price is not a memory-API price, and the model is internally
consistent only because 72% of the book is assumed to clear at a price 1.33× above anything the
category publishes — while that same 72% is priced, at the model's own cost stack, at a payback
the blended line does not show.

---

## 2. What this document does not do

- It does **not** re-derive TAM, SAM or SOM. They are carried from `inputs.json` and asserted.
- It does **not** change the blended ACV. $14,000 is the reference throughout; the findings are
  statements about what must be true for it to hold, not proposals to move it.
- It does **not** invent a competitor price. Where a vendor publishes no price, the row says
  `unpublished`. Four competitor prices are used, each read from the vendor's own page on
  2026-11-01 and carried with a source ID.
- It does **not** claim to know mem20's true willingness-to-pay. It compares published prices.
  Whether a governance buyer would pay more than an API buyer is the hypothesis under test, not
  a finding.

---

## 3. The ladder, annualised

Every competitor price is monthly-published and annualised at ×12 for comparability. mem20's
rungs are annual by construction, so no conversion is applied to them.

| Kind | Player | Plan / rung | USD / year | Share of book | × blended ACV | Gross margin | CAC payback |
|---|---|---|---:|---:|---:|---:|---:|
| published | Letta | Pro (personal) | **$240** | — | 0.02× | — | — |
| published | Zep | Flex | **$1,500** | — | 0.11× | — | — |
| published | Zep | Flex Plus | **$4,500** | — | 0.32× | — | — |
| published | Mem0 | Free | **$0** | — | 0.00× | — | — |
| published | Mem0 | Custom | *unpublished* | — | — | — | — |
| published | Zep | Enterprise | *unpublished* | — | — | — | — |
| **rung** | **mem20** | **Team** | **$6,000** | **0.72** | 0.43× | **28.7%** | **9.77 yr** |
| **rung** | **mem20** | **Business** | **$18,000** | 0.12 | 1.29× | 76.2% | 1.22 yr |
| **rung** | **mem20** | **Scale** | **$36,000** | 0.12 | 2.57× | 88.1% | 0.53 yr |
| **rung** | **mem20** | **Enterprise** | **$80,000** | 0.04 | 5.71× | 94.7% | 0.22 yr |
| blend | **mem20** | **Blended ACV** | **$14,000** | 1.00 | 1.00× | 69.43% | 1.73 yr |

Gross margin and payback are computed at `cogs_per_account_usd` = **$4,280** (hosting $1,880 +
support $2,400) and `blended_cac_usd` = **$16,800**, both from `model_output.json`. The blend
column reproduces the model exactly: 0.72·6,000 + 0.12·18,000 + 0.12·36,000 + 0.04·80,000 =
**$14,000** with no residual.

---

## 4. F1 — The ceiling is $4,500, and the ACV is 3.11× above it

Three vendors publish a self-serve price. Sorted by the highest plan each publishes:

| Vendor | Highest published plan | USD/month | USD/year |
|---|---|---:|---:|
| Zep | Flex Plus (200,000 credits) | $375 | **$4,500** |
| Zep | Flex (50,000 credits) | $125 | $1,500 |
| Letta | Pro (up to 20 stateful agents) | $20 | $240 |

Zep also publishes 10,000 free credits a month; Letta's free tier is limited to 3 stateful
agents; Mem0's free tier allows 50,000 adds and 10,000 retrievals a month on your own LLM key.
Above those, the only published motion is **"talk to us"** — both Zep's Enterprise tier and
Mem0's Custom tier are quote-only.

That makes **$4,500 a year the top of the published market.** Everything above it is negotiated
and invisible, which is precisely why this matters: a buyer comparing mem20's published ladder
to the category has no reference point between $4,500 and a conversation with sales.

Two ratios follow, and they bound the positioning problem:

- **Blended ACV ÷ ceiling = $14,000 ÷ $4,500 = 3.11×**
- **Lowest mem20 rung ÷ ceiling = $6,000 ÷ $4,500 = 1.33×**

**What this means.** The Team rung is only 33% above the most expensive self-serve plan in the
category — that is a defensible adjacency for a product with a storage-layer provenance claim
nobody else has. The **blend** at 3.11× is not adjacent to anything published; it is a
different motion entirely. The model is therefore not priced as a memory API. It is priced as
governance software, and every finding below follows from that.

---

## 5. F2 — 72% is the exact ceiling. There is no tolerance

This is arithmetic, not judgement, and it is exact in rational numbers.

Hold the non-Team rungs in their declared *relative* proportions (12:12:4, i.e. 3/7 Business,
3/7 Scale, 1/7 Enterprise). Their weighted average is **$242,000 ÷ 7 = $34,571.43**. With
Team at $6,000, the blend as a function of Team share $$x$$ is:

$$\text{blend}(x) = 6000x + 34571.43(1 - x)$$

Solving $$\text{blend}(x) = 14000$$ gives **x = 0.72 exactly** — the declared share, to the
last digit.

**The consequence is that the model has no headroom at all on mix.** Sensitivity, one direction
only (Business share moving to Team, which is what happens when PLG underperforms on expansion):

| Shift Business → Team | Blended ACV | SOM at 120 accounts | vs $1.68M | Accounts needed to hold SOM |
|---:|---:|---:|---:|---:|
| 1 pp | $13,880 | $1,665,600 | −$14,400 (−0.9%) | 121.0 |
| 5 pp | $13,400 | $1,608,000 | −$72,000 (−4.3%) | 125.4 |
| 10 pp | $12,800 | $1,536,000 | −$144,000 (−8.6%) | 131.2 |
| 20 pp | $11,600 | $1,392,000 | −$288,000 (−17.1%) | 144.8 |

The per-point delta is exactly **(18,000 − 6,000) / 100 = $120** of ACV, or **$14,400** of SOM
at 120 accounts.

**Why the two ways of reading this differ.** The accounts column is the one that matters, and it
is the benign reading: lose 10 points of mix and you need 131.2 accounts instead of 120 — 9%
more logos. The ACV column is the one that gets quoted, and it moves the revenue figure by 8.6%.
Both are correct. A model that can absorb a 10-point mix miss by selling nine more accounts is
**not** fragile. A model that is quoted as "$14,000, exact by construction" while sitting on a
zero-margin boundary is fragile *in the asset that quotes it*, because any rounding in a
downstream doc lands on the wrong side.

**The asymmetry to note.** The constraint binds in one direction only. Moving mix up-market
(Team → Business) raises the blend: 5 points up gives $14,600 and $1,752,000. So the declared
72% is a floor on quality of mix and a ceiling on volume-led growth. You can be wrong in the
good direction for free.

---

## 6. F3 — At the model's own cost stack, the Team tier does not pay back

The model publishes one blended line: 69.43% gross margin, 1.73-year payback. Those numbers are
correct *for the blend*. Applying the model's own absolute COGS and CAC to each rung separately
gives a different picture:

| Rung | ACV | Gross profit | Gross margin | CAC payback | CAC ÷ ACV |
|---|---:|---:|---:|---:|---:|
| Team | $6,000 | $1,720 | **28.7%** | **9.77 yr** | 2.80× |
| Business | $18,000 | $13,720 | 76.2% | 1.22 yr | 0.93× |
| Scale | $36,000 | $31,720 | 88.1% | 0.53 yr | 0.47× |
| Enterprise | $80,000 | $75,720 | 94.7% | 0.22 yr | 0.21× |
| **Blend** | **$14,000** | **$9,720** | **69.43%** | **1.73 yr** | 1.20× |

The blend check is exact: 0.72·1,720 + 0.12·13,720 + 0.12·31,720 + 0.04·75,720 = **$9,720**,
giving 69.43% and a 1.73-year payback — identical to `model_output.json`.

**What that reveals.** The blended CAC payback of 1.73 years is carried by the 28% of the book
above Team. For the **72% of the book sitting on Team**, the same CAC implies a **9.77-year
payback** and a **28.7% margin**. The model is arithmetically honest — it says exactly this in
`model_output.json` — but any asset that quotes "69.43% gross margin, 1.73-year payback" as an
account-level property is describing 28% of the customers and attributing it to all of them.

The gap is **40.8 percentage points of margin** and **8.04 years of payback** between the Team
rung and the blended line.

**The condition that resolves it.** Team must acquire at close to zero CAC. `inputs.json`
already declares `inbound_signals: 0` and `community_channels: 0`, and the CAC formula is
`$210/touch × 32 touches ÷ 0.40 close` — a **sales-led** cost applied to a **self-serve-priced**
tier. If Team is genuinely PLG, its CAC is not $16,800 and the 9.77-year figure dissolves. If
Team is sold by the same motion as Business, the 9.77-year figure is real and 72% of the book
is uneconomic. **The model currently applies the sales-led CAC to every rung**, so it reports
the pessimistic case and does not say so.

---

## 7. F4 — The "self-serve" slice is priced 3.11× above self-serve

`docs/finance/market_sizing.csv` splits SAM into two motions:

| Slice | Value | Accounts | Per account | Label in the file |
|---|---:|---:|---:|---|
| self-serve slice of SAM | $126,900,000 | 9,064 | **$14,000.44** | "PLG motion" |
| sales-led slice of SAM | $155,100,000 | 11,078 | $14,000.72 | "Direct motion" |

Both slices divide the same $14,000 ACV into SAM. That is internally consistent — and it is
also the problem. **The "self-serve, PLG motion" slice implies a $14,000 self-serve price**, and
the highest self-serve price published anywhere in the category is **$4,500**. The slice is
labelled a motion it cannot be priced for.

The 44 cents is worth naming so nobody reads it as a finding: $126.9M ÷ $14,000 = 9,064.28, and
the file floors to 9,064, so the division returns $14,000.44. It is the documented integer-floor
residue, not a price. The finding is the **3.11× ratio**, not the cents.

**What the slice would have to be instead.** At the category's published ceiling of $4,500, the
same $126.9M covers **28,200 accounts** — 3.11× the 9,064 the model carries. So there are two
coherent readings, and the model mixes them:

1. **Same value, lower price** — the self-serve slice is $126.9M but needs 28,200 accounts at
   $4,500, not 9,064 at $14,000. Account count triples; ACV halves.
2. **Same price, smaller value** — the self-serve slice at $14,000/account is genuinely
   governance-priced, so it is not self-serve, and the split into "PLG" and "direct" should be
   relabelled around buyer type (governance vs. platform) rather than sales motion.

Either is defensible. Carrying both labels on the same number is not.

---

## 8. F5 — The category is vacating the middle, which makes the anchor problem worse

Two events on the supply side matter for where mem20's price can sit.

**Mem0 no longer publishes a mid-market ladder.** On 2026-11-01 the live pricing page shows
exactly two cards: **Free** and **Custom**. Free is generous — 50,000 adds and 10,000 retrievals
a month once you bring your own LLM key (the first 30 days run 10,000/1,000 with Mem0's model
calls). Custom is quote-only, and its feature list is the tell: **graph memory, user profiles,
Dream memory consolidation, SSO**. Several secondary write-ups dated October 2026 still describe
a $19 Starter and a $249 Pro tier; the vendor's own page no longer offers either. **The $19–$249
band that most of the 2026 comparison literature is built on is gone from the source.**

**Zep retired its self-hosted Community Edition.** Graphiti remains Apache-2.0, but the memory
*service* is now hosted-only above a 10,000-credit free tier, metered at $125 and $375 a month
with overage at $25 per 10k and $75 per 40k credits. The free self-hosted path for the full
service no longer exists.

**Why this cuts both ways for mem20.** It removes the two cheapest escape hatches a buyer had —
"just self-host Zep" and "just pay $19". That is good for anyone selling above $4,500. But it
also means the market is bifurcating into **free** and **quote-only**, with nothing published in
between. A $6,000 Team rung lands in an empty band: too expensive to be the obvious upgrade from
a 10,000-credit free tier, too cheap and too self-serve to carry the procurement conversation
that a Custom/Enterprise quote implies. **The Team rung's real competitor is not Zep Flex Plus at
$4,500 — it is the free tier, plus the cost of the engineer who would wire it up.**

---

## 9. What must be true for $14,000 to be the right number

Stated as conditions, because each is falsifiable and each is currently assumed rather than
evidenced:

1. **Team share must not exceed 72%.** Exact, proven in §5. Any drift down-market costs $120 of
   ACV per point. This is a budget condition on growth, not a pricing condition.
2. **Team must acquire at near-zero CAC.** Otherwise 72% of the book pays back in 9.77 years
   (§6). The model's own `inbound_signals: 0` makes this a *stated* assumption, and nothing in
   the repo evidences it.
3. **The buyer must be a governance buyer, not a memory-API buyer.** No memory-API buyer pays
   3.11× the published ceiling (§4). The store-level provenance claim is the only thing in the
   reference row that justifies a different motion — and §4 of the competitive matrix already
   concedes that "nobody else does audit" is no longer a defensible sentence, since IBM
   watsonx.governance and Lyzr both ship audit at the orchestration layer. The differentiator
   has to be **provenance in the store**, not the existence of an audit trail.
4. **The self-serve slice must be relabelled or repriced** (§7). It cannot be PLG and $14,000 at
   the same time.
5. **The 3-year LTV:CAC of 2.01× must be resolved by distribution, not price.** The finance
   README already says this and already discloses that 2.01× sits below the 3.0× hurdle. Price
   is not the lever; CAC is. Cutting price to reach self-serve would lower ACV without touching
   the $16,800 CAC, which moves payback the wrong way.

**If all five hold**, $14,000 is defensible as a governance price and the ladder is sound. **If
any one fails**, the cheapest fix is not to move the price — it is to move the **cost to acquire**,
which is the only input in the model that is currently asserted with zero evidence behind it.

---

## 10. Source register

**P — published prices, read 2026-11-01.** Vendor's own page, no intermediary.

| ID | Source | Claim used | Value |
|---|---|---|---|
| P1 | `mem0.ai/pricing` | Live page shows **Free** and **Custom** only; no $19/$249 tier | Free: 50,000 adds + 10,000 retrievals/mo with own LLM key; Custom: quote-only |
| P2 | `docs.letta.com/pricing` | Personal plans: Free ($0, 3 stateful agents) and **Pro $20/mo** (up to 20 stateful agents); Developer plans usage-based; Teams/Enterprise separate | $20/mo |
| P3 | `getzep.com/pricing` | Flex **$125/mo** (50,000 credits, overage $25/10k); Flex Plus **$375/mo** (200,000 credits, overage $75/40k); Free 10,000 credits/mo; Enterprise custom | $125 / $375 per month |

**R — repository figures, reproducible from this repo.** Unchanged identifiers from
`docs/market/source-register-2026-11-01.md` where they already exist.

| ID | Figure | Value | Reproduce with |
|---|---|---|---|
| R1 | `cogs_per_account_usd` | **$4,280** | `model_output.json` → `unit_economics.cogs_per_account_usd` (hosting 1,880 + support 2,400) |
| R2 | `blended_cac_usd` | **$16,800** | `unit_economics.blended_cac_usd` |
| R3 | Blended ACV | **$14,000** | `inputs.json` → `house_numbers.blended_acv_usd` |
| R4 | Tier ladder | 6,000 / 18,000 / 36,000 / 80,000 at 72/12/12/4 | `inputs.json` → `tier_ladder` |
| R5 | Self-serve slice | $126,900,000 / 9,064 accounts | `docs/finance/market_sizing.csv` row 4 |
| R6 | Sales-led slice | $155,100,000 / 11,078 accounts | `docs/finance/market_sizing.csv` row 5 |
| R7 | Blended gross margin | 69.43% | `unit_economics.gross_margin_pct` |
| R8 | CAC payback | 1.73 yr | `unit_economics.cac_payback_years` |
| R9 | 0 inbound signals, 0 community channels | declared | `model_output.json` → `unit_economics` |

Every cell in the CSV carries a P or R identifier. No cell is unsourced. Where a vendor publishes
no price, the CSV records `unpublished` — it does not estimate a band.

---

## 11. Reproduce

```bash
python3 scripts/verify_price_ladder.py
```

The verifier recomputes every arithmetic cell in this document and in the CSV from
`inputs.json` and `model_output.json`, from nothing but the four published prices above. It is
portable (`REPO_ROOT` resolves from the script's own location) and runs from any directory.

Exit 0 = all checks pass, exit 1 = a check failed, exit 2 = a required file is missing. It
checks, among other things, that the ladder sums to $14,000 with no residual, that the Team
share ceiling solves to exactly 0.72, that the per-point mix delta is $120/$14,400, that the
published ceiling is $4,500 and the ratio is 3.11×, that the CSV and the model agree, and that
this document never states a market figure other than the four carried ones.

---

## 12. Scope limits

- **Prices are point-in-time.** Read 2026-11-01. Vendors reprice without notice — Mem0's page
  demonstrably changed under the comparison literature inside a few weeks (§8). Any reuse of
  these ratios after a reprice needs a re-read, not a carry-over.
- **Annualisation at ×12 is a convention, not a discount model.** No annual-prepay discount is
  applied to any competitor. mem20's rungs are already annual. If a competitor discounts annual
  prepay, its effective ceiling is lower than $4,500 and every ratio here gets **stronger**, so
  the finding is conservative in the direction that matters.
- **Free tiers are not compared as prices.** A $0 tier is recorded at $0 and never used in a
  ratio. Comparing a free tier to a paid rung on price alone would be a category error.
- **Published prices are the floor of the real price, not the price.** Every vendor's top tier is
  quote-only. The true enterprise ceiling is unknown to anyone outside those deals, which is
  exactly why the ratio to *published* prices is the honest one to quote.
- **This is not a demand study.** Nothing here measures whether a governance buyer would pay
  $14,000. It measures whether the price is internally consistent with the model and externally
  adjacent to anything a buyer can see. Those are necessary conditions, not sufficient ones.
- **No number in this document was derived by negotiating a competitor's price.** The $242,000/7
  weighted average in §5 is a weighted average of *mem20's own* rungs, not a market observation.

---

## 13. Decisions needed

1. **Team tier CAC.** Is Team acquired by PLG (near-zero CAC, the 9.77-year payback is
   hypothetical) or by the declared $16,800 sales motion (the payback is real and 72% of the book
   is uneconomic)? The model cannot be right about both. This is the highest-leverage open input
   in the whole model.
2. **The self-serve slice.** Reprice it at the category ceiling and carry 28,200 accounts, or keep
   $14,000/account and relabel the split by buyer type instead of by sales motion?
3. **The Team rung's job.** Is $6,000 meant to be an upgrade path from a free tier (in which case
   it sits in an empty band and needs a published price point to land on), or a sales-qualified
   entry engagement (in which case it should not be called Team)?
4. **Whether to publish a price between $4,500 and $14,000.** The category currently publishes
   nothing there. That gap is either mem20's opportunity or the reason its price looks
   arbitrary — and that is an owner call, not a research finding.

---

**SOURCE:** house figures carried from `docs/finance/inputs.json` (`house_numbers`) and
`docs/finance/model_output.json` (`unit_economics`), not re-derived. Published competitor prices
read from the vendors' own pricing pages on 2026-11-01 (P1–P3). Ladder arithmetic recomputed by
`scripts/verify_price_ladder.py` against baseline `d99ab5d8e9c5c45a1fb3d02d3b65b2f9a96b5110`.

**DISCLAIMER:** As an AI Agent, I cannot provide legally protected, personalized investment
advice. This analysis is for informational purposes only and does not constitute investment
advice or recommendations. Consult a licensed financial advisor before making investment
decisions.
