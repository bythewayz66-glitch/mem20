# Tier Ladder Sensitivity — Does the Ladder Actually Produce $14,000?

**Date:** 2026-11-01 (supersedes the 2026-10-27 pass)
**Base:** `main` @ `2ea44922`
**Directive:** `docs/ops/owner-directive-2026-11-01.md` @ `06fa1220`, row 17.
**Question:** `docs/finance/inputs.json` declares a four-tier ladder (Team $6,000 at 0.72
share, Business $18,000 at 0.12, Scale $36,000 at 0.12, Enterprise $80,000 at 0.04) and
asserts it blends to the $14,000 house ACV. Does it, and on what book?

**Verdict, up front:** the ladder reconciles **exactly in percentage space** ($14,000.00,
delta $0.00). In integer space the declared shares are not whole accounts, but the target
is **inside the admissible rounding band** — $13,983.33 to $14,233.33 — so the rounding
does not put $14,000 out of reach. The real constraint is not the rounding; it is that the
mix cannot drift by even one account in the top tiers without breaching a 1% SOM
tolerance.

Model: `docs/pricing/tier_price_derivation.py` (run with `--write`).
Data: `docs/pricing/tier-price-derivation.csv`. Every figure below is emitted by that
script and asserted present by `docs/pricing/audit_pricing_docs.py`.

> **Corrections to the 2026-10-27 version of this note.** That version reported
> $14,083.33 as *the* integer-space answer and 86/18/10/6 as the nearest exact mix. Both
> were artefacts of measuring from a single rounded book. Largest-remainder rounding is
> **not unique** at this share vector — three tiers tie — so there are three admissible
> books, and the nearest exact mix to the declared shares is **89/13/12/6**. See §3.

---

## 1. Cost baseline used throughout

Carried from `docs/finance/inputs.json` → `unit_cost_and_funnel`. Not re-derived here.

| Component | Value |
|---|---:|
| Hosting per account | $1,880 |
| Direct support (24 tickets × $100) | $2,400 |
| **COGS per account** | **$4,280** |

Gross profit per account = tier price − $4,280. This is the number that makes the tier mix
commercially interesting, as §6 shows.

---

## 2. Test 1 — percentage space: the ladder passes, and the shares are forced

This is the check the reconciliation note ran, and it is correct as far as it goes.

| Tier | ACV | Share | Weighted contribution |
|---|---:|---:|---:|
| Team | $6,000 | 0.72 | $4,320.00 |
| Business | $18,000 | 0.12 | $2,160.00 |
| Scale | $36,000 | 0.12 | $4,320.00 |
| Enterprise | $80,000 | 0.04 | $3,200.00 |
| **Blend** | — | **1.00** | **$14,000.00** |

Delta from the house figure: **$0.00**. Exact, not within tolerance.

### 2.1 The shares are not a free parameter

A weighted-sum table shows four products add up. It does not show the shares are the ones
the target *forces*. Inverting the blend does — hold three shares and solve for the fourth:

| Tier | Solve | Result | Declared |
|---|---|---:|---:|
| Team | $$(14{,}000 - 9{,}680) / 6{,}000$$ | **0.7200** | 0.72 ✓ |
| Business | $$(14{,}000 - 11{,}840) / 18{,}000$$ | **0.1200** | 0.12 ✓ |
| Scale | $$(14{,}000 - 9{,}680) / 36{,}000$$ | **0.1200** | 0.12 ✓ |
| Enterprise | $$(14{,}000 - 10{,}800) / 80{,}000$$ | **0.0400** | 0.04 ✓ |

All four return the declared share. Given these prices and this target, 72/12/12/4 is the
only share vector that closes — which is a stronger claim than "the table sums correctly".

### 2.2 Which tier carries the blend

At fixed mix, $$\partial \text{ACV} / \partial p_i = s_i$$:

| Tier | Share | A $1,000 move shifts the blend by |
|---|---:|---:|
| Team | 0.72 | **$720.00** |
| Business | 0.12 | $120.00 |
| Scale | 0.12 | $120.00 |
| Enterprise | 0.04 | $40.00 |

$$0.72 / 0.04 = 18\times$$ — the blend is 18× more sensitive to the entry tier than to the
top tier. Team +$1,000 forces Enterprise −$18,000 to hold $14,000. There is no rebalancing
that absorbs an entry-tier move; that is why the recommendation is to hold all four prices.

---

## 3. Test 2 — integer space: the target is inside the band

A share vector has to become whole accounts. $14,000 is an average over 120 logos, so
each tier's share has to be an integer number of customers.

```
0.72 × 120 = 86.4     0.12 × 120 = 14.4     0.12 × 120 = 14.4     0.04 × 120 = 4.8
```

None of those is an integer. Flooring gives **86/14/14/4 = 118** — two accounts short.

### 3.1 Largest remainder is not unique at this share vector

The fractional parts are **0.40 / 0.40 / 0.40 / 0.80**. Enterprise uniquely takes the first
leftover account. The second may go to **Team, Business or Scale** — all three tie at
0.40. So largest-remainder rounding admits **three** books, not one:

| Book | Blend | vs $14,000 | SOM | vs $1,680,000 |
|---|---:|---:|---:|---:|
| 87/14/14/5 | $13,983.33 | −$16.67 | $1,678,000 | −$2,000 |
| 86/15/14/5 | $14,083.33 | +$83.33 | $1,690,000 | +$10,000 |
| 86/14/15/5 | $14,233.33 | +$233.33 | $1,708,000 | +$28,000 |

**The band spans $13,983.33 to $14,233.33, and $14,000 is inside it.**

The 2026-10-27 version of this note reported only the middle row and called +$10,000 "the"
rounding error. That was one arbitrary tie-break out of three — and not the widest one.
The correct statement is the bracket: the rounding does not move the target out of reach,
and the largest admissible deviation is **+$28,000 (+1.67% of SOM)**.

The naive `round()` column is still worth naming, because it is the failure mode a finance
model actually hits: 86 + 14 + 14 + 5 = **119**. Rounding each tier independently
**silently deletes one account** and then divides by 120 anyway. Any implementation must
assert `sum(mix) == 120` before dividing.

### 3.2 How unique is the exact blend?

Brute-forcing every non-negative integer mix of the four tiers that sums to 120:

| | Count |
|---|---:|
| Possible mixes at 120 logos, 4 tiers | 302,621 |
| Mixes landing exactly on $14,000 | **45** |
| Share of mix space | **0.015%** |

Forty-five mixes hit $14,000 exactly, so the target is reachable — it is just not
reachable from 72/12/12/4. The nearest exact mix to the **declared share vector** is:

**89 / 13 / 12 / 6** — L1 = 7.6 accounts from 86.4/14.4/14.4/4.8.

Read that as the practical answer to "what mix reproduces $14,000": **89/13/12/6**, or any
of the other 44. What it is *not* is 72/12/12/4 — a share vector with no integer
realisation at this logo count.

---

## 4. Test 3 — how far can the mix drift before the blend breaks?

The per-account wedge is the number to carry in your head. Moving one account between two
tiers shifts the blend by $$(\text{price}_j - \text{price}_i) / 120$$:

| Pair moved | ACV step | **Per-logo effect** | 1 account = | 1% of SOM = |
|---|---:|---:|---:|---:|
| Team ↔ Business | $12,000 | **$100.00** | 0.71% of blend, $12,000 SOM | 1.40 accounts |
| Team ↔ Scale | $30,000 | **$250.00** | 1.79% of blend, $30,000 SOM | 0.56 accounts |
| Team ↔ Enterprise | $74,000 | **$616.67** | 4.40% of blend, $74,000 SOM | 0.23 accounts |

### 4.1 Drift budget by tolerance

How many accounts may move between a tier and Team before the blend leaves a stated band
of SOM:

| Tolerance | ± SOM | Team↔Business | Team↔Scale | Team↔Enterprise |
|---|---:|---:|---:|---:|
| 0.5% | ±$8,400 | 0.70 accounts | 0.28 accounts | 0.11 accounts |
| **1.0%** | **±$16,800** | **1.40 accounts** | **0.56 accounts** | **0.23 accounts** |
| 2.0% | ±$33,600 | 2.80 accounts | 1.12 accounts | 0.45 accounts |
| 5.0% | ±$84,000 | 7.00 accounts | 2.80 accounts | 1.14 accounts |

**Answer: the mix cannot drift by even one account in the top tiers without breaching a
1% SOM tolerance.** One Enterprise logo moving down to Team is −$533.33 of blend and
−$64,000 of SOM — nearly 4% of the target — and there are only five Enterprise logos in
the plan. The blend is a knife edge, not a plateau.

### 4.2 Wedge table off the middle admissible book (86/15/14/5)

| Movement | Mix | Blended ACV | Δ vs house | SOM |
|---|---|---:|---:|---:|
| Team → Business ×1 | 85/16/14/5 | $14,183.33 | +$183.33 | $1,702,000 |
| Business → Team ×1 | 87/14/14/5 | $13,983.33 | −$16.67 | $1,678,000 |
| Team → Scale ×1 | 85/15/15/5 | $14,333.33 | +$333.33 | $1,720,000 |
| Scale → Team ×1 | 87/15/13/5 | $13,833.33 | −$166.67 | $1,660,000 |
| Team → Enterprise ×1 | 85/15/14/6 | $14,700.00 | +$700.00 | $1,764,000 |
| Enterprise → Team ×1 | 87/15/14/4 | $13,466.67 | −$533.33 | $1,616,000 |

Note the asymmetry: **one lost Enterprise logo costs more SOM than four gained Team
logos recover.** That is §6's point in one line.

### 4.3 Ten points of mix — the largest single number

Shift 10 points of share (12 accounts) between the two tiers where such a shift is
plausible:

| Shift | Mix | Blended ACV | Δ vs house | SOM | Δ SOM |
|---|---|---:|---:|---:|---:|
| 12 accounts Scale → Enterprise | 86/15/2/17 | $18,483.33 | +$4,483.33 | $2,218,000 | **+$538,000 (+32.0%)** |
| 12 accounts Business → Team | 98/3/14/5 | $12,883.33 | −$1,116.67 | $1,546,000 | **−$134,000 (−8.0%)** |

A 32% SOM swing with **no pricing decision having been taken**. This is why the mix, not
the price, is the first-order lever in this model — and why the tier mix needs to be
managed as a target, not reported as an outcome.

---

## 5. What this means for the SOM $1.68M

`120 × $14,000 = $1,680,000` is arithmetically true and describes a mix (72/12/12/4
exactly) that no whole-account book can hold.

| Question | Answer |
|---|---|
| Is $1.68M wrong? | No — it is the right planning number, and $14,000 sits inside the admissible rounding band. |
| Is $1.68M achievable? | Yes, at 89/13/12/6 or one of the other 44 exact mixes. |
| Does the ladder support it? | Yes. The four prices are the lever; the blend is the consequence. |
| What must be disclosed? | That `$1.68M` is a **rounded blend at a nominal mix**, not `sum(tier price × integer accounts)`. |

**Recommendation: hold $1.68M and hold the tier prices. Disclose the rounding band.**
Changing a SOM headline by 0.6% to make an arithmetic chain close is worse than stating
the rounding — it spends credibility to buy two decimal places.

---

## 6. Gross profit by tier — where the money actually is

At the middle admissible book (86/15/14/5), with COGS $4,280:

| Tier | ACV | Logos | Revenue | GP / account | Gross profit | GM | GP share | Logo share | Leverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Team | $6,000 | 86 | $516,000 | $1,720 | $147,920 | 28.7% | 12.6% | 71.7% | **0.18×** |
| Business | $18,000 | 15 | $270,000 | $13,720 | $205,800 | 76.2% | 17.5% | 12.5% | 1.40× |
| Scale | $36,000 | 14 | $504,000 | $31,720 | $444,080 | 88.1% | **37.7%** | 11.7% | 3.24× |
| Enterprise | $80,000 | 5 | $400,000 | $75,720 | $378,600 | 94.7% | 32.2% | 4.2% | **7.72×** |
| **Total** | — | **120** | **$1,690,000** | — | **$1,176,400** | **69.6%** | 100% | 100% | — |

Three things a reviewer should take from this table:

1. **Team is 71.7% of the logos and 12.6% of the gross profit.** At 28.7% gross margin it
   is close to a customer-acquisition product. That is acceptable for land-and-expand —
   but it must not be described as a profit tier.
2. **Scale is the profit engine** (37.7% of GP from 11.7% of logos, 3.24× leverage).
   Any packaging change that moves accounts out of Scale is the most expensive kind.
3. **The replacement ratio is brutal at the top.** Replacing one Enterprise logo requires:

| Lost logo | Team logos needed | ACV replacing it | vs ACV lost |
|---|---:|---:|---:|
| 1 Business | 8.0 | $48,000 | $18,000 |
| 1 Scale | 18.4 | $108,000 | $36,000 |
| 1 Enterprise | **44.0 Team logos** | $264,000 | $80,000 |

Forty-four Team logos to replace the gross profit of one Enterprise logo — and that
trade is **SOM-positive but margin-negative**: it adds $264,000 of revenue against
$80,000, while cutting gross profit from $75,720 to $75,680. Revenue would rise 11% while
gross profit fell. **That is subsidised volume, not growth.**

### 6.1 The discount ceiling this implies

| Tier | Price | Contribution | GM | Max discount before zero contribution |
|---|---:|---:|---:|---:|
| Team | $6,000 | $1,720.00 | 28.67% | **28.67%** |
| Business | $18,000 | $13,720.00 | 76.22% | 76.22% |
| Scale | $36,000 | $31,720.00 | 88.11% | 88.11% |
| Enterprise | $80,000 | $75,720.00 | 94.65% | 94.65% |

**The binding cap is Team at 28.67%.** A generic 30%+ approval band would let a rep price
the entry tier below the cost of serving it. The discount policy has to be tier-specific,
not a single ladder of approval levels.

---

## 7. ±20% price band at the declared mix

The mandated sensitivity, on the fixed 120-logo plan:

| Blended ACV | vs house | SOM revenue | Gross profit | GP / account | Blended GM |
|---|---:|---:|---:|---:|---:|
| $11,200 (−20%) | −$2,800 | $1,344,000 | $830,400 | $6,920 | 61.8% |
| $12,600 (−10%) | −$1,400 | $1,512,000 | $998,400 | $8,320 | 66.0% |
| **$14,000 (held)** | **$0** | **$1,680,000** | **$1,166,400** | **$9,720** | **69.4%** |
| $15,400 (+10%) | +$1,400 | $1,848,000 | $1,334,400 | $11,120 | 72.2% |
| $16,800 (+20%) | +$2,800 | $2,016,000 | $1,502,400 | $12,520 | 74.5% |

Read as arithmetic on a fixed logo count, **not** an elasticity curve — consistent with
the reconciliation note. The band moves revenue one-for-one. The SOM base row
($1,166,400) ties exactly to the reconciliation note's §6 base row, which is the
doc-to-model check.

---

## 8. Conclusions and recommendation

1. **The ladder is sound; the blend is a convention.** Percentage space reconciles to
   $14,000 exactly, and the shares are forced by the target rather than chosen.
2. **The target is inside the rounding band.** $13,983.33 to $14,233.33; $14,000 sits
   inside it. The previous note's +$10,000 was one of three admissible tie-breaks, not
   the answer. Disclose the band, do not re-baseline.
3. **The drift tolerance is the real risk, not the rounding.** At a 1% SOM tolerance the
   blend survives 1.4 Business accounts, 0.56 Scale, or 0.23 Enterprise. There is no
   meaningful safety margin in the top tiers.
4. **Manage the mix, not just the price.** A 10-point shift between the top two tiers is
   worth $538,000 of SOM (+32%) with no pricing decision taken — 4× more than the entire
   ±20% price band at the low end.
5. **Protect Scale.** It is 11.7% of logos and 37.7% of gross profit. It is also the tier
   a discount is most likely to be aimed at.
6. **Cap discounts at the tier's own margin.** Team's ceiling is 28.67%; a 30% approval
   band would let the entry tier go contribution-negative.
7. **Never quote $14,000.** It is a blend, not a price. The quotable objects are the four
   tier prices.

**Decision: HOLD the tier prices and HOLD $1.68M, with the rounding band disclosed.**

---

## 9. Tool surface — 270 / 27, and what the gate catches

The live surface is **270 tools / 27 domains**, derived from the MCP server that registers
it rather than quoted from a doc:

| Measurement | Value |
|---|---:|
| Registration sites (`self.tools["…"]`) | 271 |
| Distinct tool names | **270** |
| `register_*_tools` groups | 28 |
| Domains (28 − 1 A2A transport) | **27** |

The 271 → 270 gap is the duplicate `lie_status` assignment
(`mcp/tools/lie_tools.py:69` and `:77`). `257/26` and `268/26` are both retired.

`audit_acv_consistency.py` enforces the surface invariant over the canonical `docs/` tree
only, with a retirement-marker escape hatch, so it fires on drift and not on history. It
catches `268/26` (the intermediate surface nobody remembers is retired) as well as
`257/26`, and it catches the bare `26 domains` phrasing that survives when someone updates
the tool count and forgets the domain count.

Measured on this base: **258** retired-surface mentions on disk, of which **82** carry a
retirement marker and **176** are present tense and unmarked. The canonical `docs/` tree
accounts for **23** of the unmarked ones; the rest are `published/` archive, where a
retired number is a record rather than drift. Those 23 belong to their own workstreams and
are not fixed here — what this branch buys is that the next author cannot add a
twenty-fourth without CI saying so.

---

## 10. What changed in this commit

| File | Change |
|---|---|
| `docs/pricing/tier-sensitivity.md` | **Rewritten.** §3 corrected: largest remainder is non-unique, the target is inside the band, and the nearest exact mix is 89/13/12/6. §9 reconciled to 270/27 with measured counts. |
| `docs/pricing/tier_price_derivation.py` | **New.** The derivation model; every figure above is printed by it. |
| `docs/pricing/tier-price-derivation.csv` | **New.** Model output. |
| `docs/pricing/audit_pricing_docs.py` | **New.** Doc-to-model figure audit plus the surface gate. |
| `docs/pricing/RECONCILIATION_NOTE.md` | **Rewritten.** Arithmetic shown; §4 corrected; §7 reconciled to 270/27. |

No number outside `docs/pricing/` was modified. The $14,000 / $1.68M / TAM / SAM house
figures are carried verbatim.

---

**Carried verbatim:** blended ACV $14,000 · TAM $1.28B / SAM $282M / SOM $1.68M ·
tool surface **270/27** (257/26 and 268/26 retired) · COGS $4,280/account.
