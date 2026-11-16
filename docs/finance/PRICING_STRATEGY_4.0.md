# mem20 4.0 — Pricing Strategy: packaging, willingness-to-pay, margin structure

**Release:** 4.0.0 · **As of:** 2026-11-16 · **Surface:** 487 tools / 129 domains
**Prepared by:** Pricing Analyst · **Model:** [`pricing_model_v4.py`](pricing_model_v4.py)
**Status:** Scenario A is committed and CI-asserted. Scenario B is a **proposal** that
requires owner sign-off because it moves a house number.

---

## 1. Executive summary

**The recommendation, in one line:** keep the four list prices, stop giving the
governance capability away inside the entry tier, and add a genuine land tier below
$6,000 — because mem20 currently has no price point a developer-memory buyer has ever
transacted at.

| # | Finding | Number | Action |
|---|---|---|---|
| 1 | mem20's entry tier is **above the entire published memory-API market** | Team $6,000 vs category ceiling $4,500 (Zep Flex Plus) = **+33%** | Add a land tier; do not cut Team |
| 2 | The governance capability is **bundled into the entry tier** | **$288,960** forgone gross profit/yr (24.56% of Scenario A GP) | Move the epistemic partition to Business |
| 3 | Gross profit is **concentrated in the top two tiers** | Scale + Enterprise = **69.9%** of GP on **15.8%** of logos | Protect Scale/Enterprise; they are the business |
| 4 | The entry tier is **margin-thin and discount-fragile** | Team GM **28.67%**; a 28.67% discount makes it contribution-negative | Cap Team discounts at 8.67% |
| 5 | A 10% list cut is **gross-profit-negative** at the assumed elasticity | break-even elasticity **−1.68** vs assumed **−0.8** | Control discount depth, not list price |
| 6 | Repackaging (Scenario B) is worth **+21.93% gross profit** | GP $1,176,400 → $1,434,400 | Owner decision — it moves the blend to $16,040 |

**What we gain from Scenario B:** +$258,000 gross profit per year on the same 120
accounts, and a blended gross margin up from 69.61% to 73.63%.
**What we risk:** the blend moves from $14,000 to $16,040, which restates SOM from
$1.68M to $1.9248M. That is a house number, so it is an owner decision, not a model
decision. The model reports the delta and never writes it into `inputs.json`.

---

## 2. Cost structure — the floor

Every price in this document sits on the same fully-loaded unit cost. It is carried
from `compute_model.py`, not re-derived here.

| Component | USD/account/yr | Basis |
|---|---:|---|
| Hosting | 1,880 | declared, `inputs.json` |
| Support | 2,400 | 24 tickets × $100 × (1 − 0 deflection) |
| **COGS** | **4,280** | hosting + support |
| Blended CAC | 16,800 | 32 touches × $210 ÷ 0.40 close, 0 inbound signals |
| CAC payback | 1.73 yr | CAC ÷ gross profit per account |

**Two things to flag about this cost base.**

1. **COGS is flat across tiers.** The model charges every tier the same $4,280. That is
   the committed assumption, and it is conservative in the direction that matters: a
   real tier-varying COGS would make Team *more* profitable (fewer seats, less support)
   and Enterprise *less* profitable (BYOC, named TAM, custom SLA). The margin
   concentration in §5 is therefore, if anything, understated for Team and overstated
   for Enterprise.
2. **CAC is the real constraint, not COGS.** At $16,800 CAC against $1,720 of Team gross
   profit, a Team logo takes **9.77 years** to pay back its acquisition cost. Team is not
   a customer-acquisition tier at this cost structure — it is a customer-acquisition
   *liability*. That is the single most important number in this document, and it is why
   finding #1 (no land tier) is not a growth problem but a unit-economics problem.

---

## 3. Willingness-to-pay evidence

### 3.1 Method, and its limits

This is a **Van Westendorp-style proxy over published competitor price points**, computed
**per segment**. It is not primary research. It answers *"where does each budget line
actually transact"* — not *"what would a mem20 buyer say in an interview"*. Vendors that
publish no price (Mem0 Custom, Zep Enterprise, Cognee Enterprise, ServiceNow) are
**excluded rather than estimated**; inventing a "six figures" band for a quote-only vendor
was the main defect in the v3 matrix and is not repeated here.

**Why the segments are kept apart.** A vector-store minimum and a governance-platform tier
are not memory-API prices. Folding them into one distribution would manufacture a ceiling
no memory buyer ever agreed to pay. Only the `memory_api` segment sets the category
ceiling.

### 3.2 The published points

| Player | Plan | USD/yr | Source | Segment |
|---|---|---:|---|---|
| Mem0 | Hobby | 0 | S1 | memory_api |
| Letta | Pro (personal) | 240 | S2 | memory_api |
| Zep | Flex | 1,500 | S5 | memory_api |
| Mem0 | Pro | 2,988 | S2 | memory_api |
| Zep | Flex Plus | 4,500 | S5 | memory_api |
| Pinecone | Standard (min) | 600 | S19 | substrate |
| Weaviate | Plus | 3,360 | S23 | substrate |
| Lyzr | platform top tier | 11,988 | S29 | governance |

Source IDs resolve in [`docs/market/source-register-2026-11-01.md`](../market/source-register-2026-11-01.md).

### 3.3 The two meters

| Meter | n | Median | Ceiling |
|---|---:|---:|---:|
| **memory_api** | 5 | $1,500 | **$4,500** |
| substrate | 2 | $1,980 | $3,360 |
| governance | 1 | $11,988 | $11,988 |

### 3.4 What this says about mem20's ladder

| mem20 tier | Price | vs memory-API ceiling | vs governance anchor |
|---|---:|---:|---:|
| Team | $6,000 | **+33%** | — |
| Business | $18,000 | +300% | **+50%** |
| Scale | $36,000 | +700% | +200% |
| Enterprise | $80,000 | +1,678% | +567% |

**Finding 1 — mem20 has no land tier.** 100% of published memory-API price points sit at
or below $6,000. The category's top published price is $4,500. A developer evaluating
mem20 against Zep or Mem0 sees an entry price **33% above the most expensive thing in the
market**, with no cheaper way in. Combined with the 9.77-year Team CAC payback, this is a
structural acquisition problem: the tier that is supposed to land customers is priced out
of the market *and* cannot pay for its own acquisition.

**Finding 2 — the governance capability is priced correctly at Business and given away at
Team.** The audit/control budget line transacts at $11,988–$12,000 (Lyzr platform top
tier, S29). Business at $18,000 is +50% versus that anchor — defensible for a capability
that is a *property of the store* rather than a layer beside it. But Team at $6,000
includes the same epistemic partition, provenance ledger and contamination audit. That is
the leak quantified in §4.

**Caveat on the governance anchor.** It rests on a single published point (n=1). It is
directionally useful — it establishes that a governance budget line exists at roughly
$12K — but it is not a distribution. Treat the +50% as an order of magnitude, not a
measurement.

---

## 4. Margin structure and the leak

### 4.1 Scenario A — the committed ladder (72/12/12/4)

| Tier | ACV | Accounts | COGS | GP/acct | GM% | Revenue | GP | GP share | GP leverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Team | 6,000 | 86 | 4,280 | 1,720 | 28.67% | 516,000 | 147,920 | 12.57% | **0.18×** |
| Business | 18,000 | 15 | 4,280 | 13,720 | 76.22% | 270,000 | 205,800 | 17.49% | 1.40× |
| Scale | 36,000 | 14 | 4,280 | 31,720 | 88.11% | 504,000 | 444,080 | 37.75% | 3.23× |
| Enterprise | 80,000 | 5 | 4,280 | 75,720 | 94.65% | 400,000 | 378,600 | 32.18% | 7.72× |
| **Total** | **14,083.33** | **120** | | | **69.61%** | **1,690,000** | **1,176,400** | 100% | |

*GP leverage = share of gross profit ÷ share of logos. Below 1.0× means the tier consumes
more logo effort than it returns in margin.*

**Finding 3 — the business is the top two tiers.** Scale and Enterprise are 15.8% of logos
and **69.9% of gross profit**. Team is 71.7% of logos and 12.6% of gross profit, at 0.18×
leverage. Any pricing move that protects Team at the expense of Scale or Enterprise is
destroying the thing that pays for everything else.

**Finding 4 — Team is discount-fragile.** At 28.67% gross margin, a 28.67% discount makes
Team contribution-negative. There is no room to negotiate on the entry tier, which is
precisely the tier where sales teams habitually discount hardest to "get a logo in".

### 4.2 The governance leak, quantified

| Item | Value |
|---|---:|
| Team accounts | 86 |
| Assumed attach rate (would pay for governance separately) | 28% |
| Eligible accounts | 24.08 |
| Uplift per account (Business − Team) | $12,000 |
| **Forgone revenue / gross profit** | **$288,960** |
| As % of Scenario A gross profit | **24.56%** |

**Mechanism:** the governance capability is included in Team at $6,000 instead of sold at
Business at $18,000. Because COGS is flat per account in this model, forgone revenue and
forgone gross profit are the same number; with tier-varying COGS the gross-profit figure
would be the smaller of the two.

**The attach rate is an assumption, not a measurement** (28%, stress-tested 15–45%). At
15% the leak is $154,800; at 45% it is $464,400. Even at the bottom of that range the leak
exceeds the entire Team tier's gross profit contribution. **This is the single largest
pricing error in the current ladder.**

---

## 5. Recommended packaging

### 5.1 Scenario B — proposed 4.0 repackaging (58/24/14/4)

Same four list prices. The only change is **what is gated into each tier**.

| Tier | Gate | ACV | Share | Accounts | GM% | GP | GP share |
|---|---|---:|---:|---:|---:|---:|---:|
| Team | core memory, full 129-domain read surface, **90-day ledger retention**, no epistemic partition | 6,000 | 58% | 69 | 28.67% | 118,680 | 8.27% |
| Business | **+ epistemic partition, unlimited ledger retention, contamination audit, evidence-based promotion** | 18,000 | 24% | 29 | 76.22% | 397,880 | 27.74% |
| Scale | + A2A transport, multi-region, SSO/SCIM, 99.9% SLA | 36,000 | 14% | 17 | 88.11% | 539,240 | 37.59% |
| Enterprise | + BYOC, custom domains, 99.95% SLA, named TAM | 80,000 | 4% | 5 | 94.65% | 378,600 | 26.39% |
| **Total** | | **16,040** | 100% | **120** | **73.63%** | **1,434,400** | 100% |

### 5.2 Scenario A vs B

| Metric | A (committed) | B (proposed) | Delta |
|---|---:|---:|---:|
| Blended ACV (fractional) | $14,000 | $16,040 | **+$2,040 (+14.57%)** |
| Blended ACV (integer book) | $14,083.33 | $16,233.33 | +$2,150 |
| Revenue | $1,690,000 | $1,948,000 | +$258,000 |
| Gross profit | $1,176,400 | $1,434,400 | **+$258,000 (+21.93%)** |
| Blended gross margin | 69.61% | 73.63% | **+4.02pp** |
| SOM ARR | $1,680,000 | $1,924,800 | +$244,800 |
| Team GP leverage | 0.18× | 0.14× | −0.04× |
| Business GP leverage | 1.40× | 1.15× | −0.25× |

**Why the blend moves.** Gating governance out of Team pulls 14% of the book up a tier.
The blend rises above $14,000, which restates SOM. **This is why Scenario B needs owner
sign-off and is not written into `inputs.json`.** The model reports the delta; it does not
adopt it.

**The honest counter-argument.** Scenario B assumes the mix shift happens without losing
logos. If gating governance out of Team pushes price-sensitive buyers out entirely rather
than up a tier, the revenue gain evaporates. The model does not test that — it is a
demand-side question that needs a real win/loss study, not a spreadsheet. **Recommendation:
run Scenario B as a controlled pilot on new logos only, grandfather existing Team accounts,
and measure the tier-migration rate before committing.**

### 5.3 The land tier (recommended addition)

Neither scenario fixes Finding 1. The recommendation is a **fifth tier below Team**:

| Proposed | Price | Contents | Purpose |
|---|---:|---|---|
| **Starter** | **$2,400/yr** | core memory, read surface, 30-day retention, single region, community support | land developers at a price the category actually transacts at |

At $2,400 the tier sits **below the memory-API median ($1,500 is the median; $2,400 is
between Zep Flex and Mem0 Pro)** and inside the published range. It is a land-and-expand
tier, not a margin tier: at $4,280 COGS it is **contribution-negative by $1,880 per
account**. That is deliberate and it must be governed:

- **Hard cap on Starter volume** — no more than 15% of the book, or the tier becomes a
  subsidy rather than a funnel.
- **Mandatory expansion path** — 30-day retention and single-region are the upgrade
  triggers; the tier must be designed so that production use forces a move to Team.
- **No Starter discounts, ever** — it is already below cost.

**Do not ship Starter without the volume cap.** A contribution-negative tier with no cap
is how margin-blind companies scale themselves into bankruptcy.

---

## 6. Sensitivity analysis

### 6.1 ±20% price grid (Scenario A base, elasticity −0.8)

| Price | Δ | Volume × | Accounts | Revenue | Gross profit | GM% | Win rate | Rev vs base | GP vs base |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| $11,200 | −20% | 1.16 | 139.2 | 1,559,040 | 963,264 | 61.79% | 39.44% | −7.20% | **−17.42%** |
| $12,600 | −10% | 1.08 | 129.6 | 1,632,960 | 1,078,272 | 66.03% | 36.72% | −2.80% | **−7.56%** |
| **$14,000** | **0%** | 1.00 | 120.0 | **1,680,000** | **1,166,400** | 69.43% | 34.00% | 0% | 0% |
| $15,400 | +10% | 0.92 | 110.4 | 1,700,160 | 1,227,648 | 72.21% | 31.28% | +1.20% | **+5.25%** |
| $16,800 | +20% | 0.84 | 100.8 | 1,693,440 | 1,262,016 | 74.52% | 28.56% | +0.80% | **+8.20%** |

**Reading the grid.** The revenue curve is nearly flat across ±20% — revenue peaks at
+10% and is *lower* at +20%. But the **gross-profit curve is monotonic**: every step up in
price adds gross profit, every step down destroys it. At −20% you lose 17.4% of gross
profit to buy 16% more volume. **This is the classic underpricing trap: revenue looks
stable while margin bleeds.**

### 6.2 Break-even elasticity

A 10% list cut holds gross profit only while elasticity is shallower than **−1.68**. At
the assumed **−0.8** the cut is gross-profit-negative. In other words: **mem20 would need
to be more than twice as price-sensitive as assumed for a 10% cut to pay for itself.**

**The elasticity is an analyst assumption, not a measurement.** It is the weakest input in
this model and it is flagged as such. The direction of the conclusion is robust across the
plausible range (−0.2 to −2.0): only at the extreme price-sensitive end does discounting
become gross-profit-neutral. **Recommendation: instrument win/loss by price point before
making any list-price move.**

### 6.3 Discount governance

Policy: **cap = gross margin − 20pp; never discount a tier below 20% of its list gross
profit.**

| Tier | GM% | Absolute cap | Policy cap | Approval |
|---|---:|---:|---:|---|
| **Team** | 28.67% | 28.67% | **8.67%** | Sales rep |
| Business | 76.22% | 76.22% | 56.22% | CEO/CFO |
| Scale | 88.11% | 88.11% | 68.11% | CEO/CFO |
| Enterprise | 94.65% | 94.65% | 74.65% | CEO/CFO |

**The binding constraint is Team at 8.67%.** Any Team discount above 8.67% eats more than
20pp of the tier's list gross profit; above 28.67% the tier is contribution-negative.

**Discount alternatives, preferred over price cuts** (all preserve list price and therefore
price realization): extended payment terms, additional retention/regions at no cost,
implementation credits, training packages, volume-commitment pricing.

---

## 7. Implementation plan

| Phase | Action | Owner | Success metric |
|---|---|---|---|
| 1 | Cap Team discounts at 8.67%; require manager approval above it | Sales | Average Team discount depth ≤ 8.67% |
| 2 | Move epistemic partition + provenance ledger to Business for **new logos only** | Product + Sales | Tier-migration rate ≥ 20% of new Team-intent deals |
| 3 | Grandfather existing Team accounts at current capability for 12 months | Sales | Incremental churn < 5% |
| 4 | Pilot Starter at $2,400 with a 15% volume cap | Product | ≥ 30% of Starter accounts upgrade within 12 months |
| 5 | Instrument win/loss by price point; replace the assumed elasticity with measured data | RevOps | Elasticity measured, not assumed |
| 6 | Review cadence: quarterly price review, monthly discount-depth report | Finance | Price realization > 85% |

**Grandfathering policy.** Existing Team accounts keep the governance capability for 12
months from the change date. This is not generosity — it is churn protection. The
incremental churn from a capability removal is the one number that can turn Scenario B's
+21.93% gross profit into a loss, and 12 months of grandfathering buys the data to measure
it.

**Price realization target.** Actual revenue ÷ list-price revenue > 85%. Below that, the
list price is fiction and the discount policy is not being enforced.

---

## 8. What this model does not know

Stated plainly, because a pricing model that hides its gaps is worse than no model:

1. **Elasticity is assumed (−0.8), not measured.** The break-even is −1.68. This is the
   weakest input.
2. **The governance attach rate is assumed (28%), not measured.** The leak ranges
   $154,800–$464,400 across the plausible band.
3. **The governance anchor rests on one published point (n=1).** Directionally useful,
   not a distribution.
4. **COGS is flat across tiers.** A tier-varying COGS would change the margin
   concentration.
5. **Scenario B assumes the mix shift without logo loss.** Untested; needs a pilot.
6. **No primary WTP research.** No Van Westendorp interviews, no conjoint, no Gabor-Granger
   on actual mem20 buyers. The published-points proxy is a substitute, not an equivalent.
7. **Win rate at list (34%) is assumed.** Used only to shape the sensitivity curve, never
   stated as an actual win rate.

---

## 9. Reproducing this

```bash
python3 docs/finance/pricing_model_v4.py --check   # verify invariants, write nothing
python3 docs/finance/pricing_model_v4.py           # verify + regenerate all artefacts
```

Artefacts written:

| File | Contents |
|---|---|
| `pricing_model_4.0.json` | full model, both scenarios, all assumptions |
| `pricing_packaging_4.0.csv` | tier gates, prices, shares, leverage, both scenarios |
| `pricing_wtp_evidence_4.0.csv` | published price points with source IDs and segments |
| `pricing_margin_structure_4.0.csv` | per-tier contribution and concentration |
| `pricing_sensitivity_4.0.csv` | ±20% grid with volume response and win rate |

**Invariants asserted on every run** (the model exits non-zero rather than emit a drifted
figure): Scenario A fractional blend = $14,000; Scenario B fractional blend = $16,040;
shares sum to 1.0; both books are exactly 120 accounts; the house SOM identity
120 × $14,000 = $1,680,000 holds.

**House numbers are never written by this model.** TAM ($1.28B), SAM ($282M), SOM
($1.68M) and blended ACV ($14,000) are read from `inputs.json` and treated as inputs.
Scenario B's blend delta is reported, not adopted.

---

*As an AI Agent, I cannot provide legally protected, personalized investment advice. This
analysis is for informational purposes only and does not constitute investment advice or
recommendations. Consult a licensed financial advisor before making investment decisions.*
