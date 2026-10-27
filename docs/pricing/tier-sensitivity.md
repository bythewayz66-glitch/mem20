# Tier Ladder Sensitivity — Does the Ladder Actually Produce $14,000?

**Date:** 2026-10-27
**Branch:** `fix/ws2-pricing-tier-sensitivity`
**Question:** `docs/finance/inputs.json` declares a four-tier ladder (Team $6,000 at 0.72
share, Business $18,000 at 0.12, Scale $36,000 at 0.12, Enterprise $80,000 at 0.04) and
asserts it blends to the $14,000 house ACV. It has never been tested. This note tests it.

**Verdict, up front:** the ladder reconciles **exactly in percentage space and nowhere
else**. On a real 120-logo book the declared percentages are not whole accounts, and the
nearest honest whole-account mix lands **$83.33 per logo high** ($14,083.33), which is
**$10,000 of SOM above the $1.68M house figure**. The drift tolerance is under two
accounts in the upper tiers. The ladder is a valid pricing structure; `$14,000` is a
rounding convention applied to it, not an output of it.

Model: `docs/pricing/tier_sensitivity_model.py` (run with `--write`).
Data: `docs/pricing/tier-sensitivity.csv`. Every figure below is emitted by that script.

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

## 2. Test 1 — percentage space: the ladder passes

This is the check the reconciliation note ran, and it is correct as far as it goes.

| Tier | ACV | Share | Weighted contribution |
|---|---:|---:|---:|
| Team | $6,000 | 72% | $4,320.00 |
| Business | $18,000 | 12% | $2,160.00 |
| Scale | $36,000 | 12% | $4,320.00 |
| Enterprise | $80,000 | 4% | $3,200.00 |
| **Blend** | — | **100%** | **$14,000.00** |

Delta from the house figure: **$0.00**. Exact, not within tolerance.

So the ladder is internally consistent. The question is whether that consistency
survives contact with a logo count.

---

## 3. Test 2 — integer space: the ladder fails

A share vector has to become whole accounts. $14,000 is an average over 120 logos, so
each tier's share has to be an integer number of customers.

```
72% × 120 = 86.4     12% × 120 = 14.4     12% × 120 = 14.4     4% × 120 = 4.8
```

None of those is an integer. Three ways of resolving that, and what each does to the
house number:

| Rounding method | Mix | Sums to 120? | Blended ACV | vs $14,000 |
|---|---|---:|---:|---:|
| Naive `round()` per tier | 86 / 14 / 14 / 5 | **119 — invalid** | — | loses an account |
| **Largest remainder** | **86 / 15 / 14 / 5** | **120** | **$14,083.33** | **+$83.33** |
| Declared percentages, read literally | 86.4 / 14.4 / 14.4 / 4.8 | 120 | $14,000.00 | $0 — not an integer mix |

The naive `round()` column is worth naming explicitly: 86 + 14 + 14 + 5 = 119. A finance
model that rounds each tier independently **silently deletes one account** and then
divides by 120 anyway. Largest-remainder rounding is the only method that preserves the
book, and it lands on **86/15/14/5**.

That reachable mix is the one used for the rest of this note:

| | Blended ACV | SOM revenue | GP / account | SOM gross profit |
|---|---:|---:|---:|---:|
| House figure | $14,000.00 | $1,680,000 | $9,720.00 | $1,166,400 |
| Reachable mix 86/15/14/5 | **$14,083.33** | **$1,690,000** | **$9,803.33** | **$1,176,400** |
| Delta | +$83.33 | **+$10,000 (+0.60%)** | +$83.33 | +$10,000 |

**This is the finding.** Not that the ladder is wrong — that `120 × $14,000 = $1,680,000`
and `86/15/14/5 of the same four tiers = $1,690,000` are two different worlds, and the
repo currently states both without acknowledging the gap. The gap is 0.60% of SOM. It is
immaterial to any decision, and it is not zero. It should be disclosed rather than
rounded away, because the next reviewer will find it.

### 3.1 How unique is the exact blend?

Brute-forcing every non-negative integer mix of the four tiers that sums to 120:

| | Count |
|---|---:|
| Possible mixes at 120 logos, 4 tiers | 302,621 |
| Mixes landing exactly on $14,000 | **45** |
| Share of mix space | **0.015%** |

Forty-five mixes hit $14,000 exactly, so the target is reachable — it is just not
reachable from 72/12/12/4. The nearest exact mix to the declared one is
**86 / 18 / 10 / 6** (8 accounts of movement away), and it blends to $14,000.00.

Read that as the practical answer to "what mix reproduces $14,000": **86/18/10/6**, or any
of the other 44. What it is *not* is 72/12/12/4 — a share vector that has no integer
realisation at this logo count.

---

## 4. Test 3 — how far can the mix drift before the blend breaks?

The per-account wedge is the number to carry in your head. Moving one account between two
tiers shifts the blend by `(price difference) / 120`:

| Pair moved | ACV step | **Per-logo effect** | 1 account = | $1 of SOM = |
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

### 4.2 Wedge table off 86/15/14/5 (one account at a time)

| Movement | Mix | Blended ACV | Δ vs house | SOM |
|---|---|---:|---:|---:|
| Team → Business ×1 | 85/16/14/5 | $14,183.33 | +$183.33 | $1,702,000 |
| Business → Team ×1 | 87/14/14/5 | $13,983.33 | −$16.67 | $1,678,000 |
| Team → Scale ×1 | 85/15/15/5 | $14,333.33 | +$333.33 | $1,720,000 |
| Scale → Team ×1 | 87/15/13/5 | $13,833.33 | −$166.67 | $1,660,000 |
| Team → Enterprise ×1 | 85/15/14/6 | $14,700.00 | +$700.00 | $1,764,000 |
| Enterprise → Team ×1 | 87/15/14/4 | $13,466.67 | −$533.33 | $1,616,000 |

Note the asymmetry: **one lost Enterprise logo costs more SOM than four gained Team
logos recover.** That is §5's point in one line.

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

`120 × $14,000 = $1,680,000` is arithmetically true and describes a mix
(72/12/12/4 exactly) that no whole-account book can hold.

| Question | Answer |
|---|---|
| Is $1.68M wrong? | No — it is the right planning number, and it is within 0.60% of the reachable mix. |
| Is $1.68M achievable? | Yes, at 86/18/10/6 or one of the other 44 exact mixes. At 86/15/14/5 it is $1,690,000. |
| Does the ladder support it? | Yes. The four prices are the lever; the blend is the consequence. |
| What must be disclosed? | That `$1.68M` is a **rounded blend at a nominal mix**, not `sum(tier price × integer accounts)`. |

**Recommendation: hold $1.68M and hold the tier prices. Disclose the $10,000 rounding.**
Changing a SOM headline by 0.6% to make an arithmetic chain close is worse than stating
the rounding — it spends credibility to buy two decimal places.

---

## 6. Gross profit by tier — where the money actually is

At the reachable 86/15/14/5 mix, with COGS $4,280:

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
| 1 Enterprise | **44.0** | $264,000 | $80,000 |

Forty-four Team logos to replace the gross profit of one Enterprise logo — and that
trade is **SOM-positive but margin-negative**: it adds $264,000 of revenue against
$80,000, while cutting gross profit from $75,720 to $75,680. Revenue would rise 11% while
gross profit fell. **That is subsidised volume, not growth.**

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
($1,166,400) ties exactly to the reconciliation note's §3 base row, which is the
doc-to-model check.

---

## 8. Conclusions and recommendation

1. **The ladder is sound; the blend is a convention.** Percentage space reconciles to
   $14,000 exactly. Integer space does not, and cannot, from 72/12/12/4.
2. **State the rounding.** $1.68M is `120 × $14,000` at a nominal mix. The reachable
   realisation is $1,690,000 at 86/15/14/5 (+0.60%), or $1,680,000 exactly at 86/18/10/6.
   Disclose, do not re-baseline.
3. **The drift tolerance is the real risk, not the rounding.** At a 1% SOM tolerance the
   blend survives 1.4 Business accounts, 0.56 Scale, or 0.23 Enterprise. There is no
   meaningful safety margin in the top tiers.
4. **Manage the mix, not just the price.** A 10-point shift between the top two tiers is
   worth $538,000 of SOM (+32%) with no pricing decision taken — 4× more than the entire
   ±20% price band at the low end.
5. **Protect Scale.** It is 11.7% of logos and 37.7% of gross profit. It is also the tier
   a discount is most likely to be aimed at.
6. **Never quote $14,000.** It is a blend, not a price. The quotable objects are the four
   tier prices.

**Decision: HOLD the tier prices and HOLD $1.68M, with the rounding disclosed.**

---

## 9. Known audit output — pre-existing false positives, named not hidden

Running `python3 docs/pricing/audit_acv_consistency.py --no-surface` currently exits 1 on
five lines. **None is ACV drift**, and all five predate this branch. They are named here
so the next reader does not mistake them for new findings:

| Location | What it really is |
|---|---|
| `docs/finance/reconciliation_log.csv:4` | `SOM ARR (accounts x ACV),1680000.0,...` — a CSV cell boundary. The connector crosses `),` and reads the SOM as an ACV. |
| `docs/finance/reconciliation_log.csv:5` | Same boundary effect on the TAM account row. |
| `docs/finance/reconciliation_log.csv:6` | Same boundary effect on the SAM account row. |
| `docs/pricing/RECONCILIATION_NOTE.md:15` | `$2,011` is a **file count** ("Files scanned for ACV claims"), not money. |
| `published/checkpoints/ledger.md:35` | `$340` is a fragment of a commit SHA (`d340a3a5…`) in a ledger table. |

The correct fix is a connector that refuses to cross `)` and `,` — the two characters that
carry CSV and markdown table structure — plus a 3-digit floor on un-prefixed money tokens.
That is a change to the *ACV matcher*, which this note deliberately does not make: the ACV
invariant was reconciled at 44/44 and re-litigating its parser is out of scope here. What
this branch does change is the **surface** gate, which is new and which does fire on real
content (see §10).

**Honest status: the ACV invariant is unchanged and still verified; the extended gate's
new surface check works; five known parser false positives remain open and are listed
above with their causes.**

## 10. Surface-drift gate — what the extension catches

`audit_acv_consistency.py` now also enforces the **tool-surface** invariant, which it
previously ignored entirely. Live surface is **270 tools / 27 domains**; `257/26` and
`268/26` are both retired.

The check is scoped so it fires on drift and not on history:

- **Scope:** the canonical `docs/` tree only, reusing the ACV sweep's `SKIP_DIRS`.
  `published/` is archive — a retired number there is a record, not drift.
- **Excluded by name:** `CHANGELOG.md`, `DIARY.md`, `CANONICAL.md` and `docs/pricing/`,
  whose job is to narrate retired numbers.
- **Escape hatch:** a retirement marker (`retired`, `superseded`, `was 257`, `legacy`,
  `previously`, `stale`, …) within ±2 lines marks the mention as deliberate history.

On this branch it fires on **15 live lines** that state a retired surface in the present
tense — `docs/05-complete-tools-reference.md` (6), `docs/sdk/cpp/source-ledger.md` (2),
`docs/gtm/README.md` (2), and one each in `docs/gtm/claim-ledger.md`,
`docs/gtm/mem20-campaign-plan.md`, `docs/02-tools-reference.md`,
`docs/audit/2026-10-repository-audit.md` and
`docs/troubleshooting-mcp-server-startup.md`. Those are real pre-existing drift in
other owners' files and are **not** fixed here — each belongs to its own workstream. What
this branch buys is that the next author can no longer add a sixteenth without CI saying
so.

Two behaviours worth noting, because they are what makes the gate useful rather than
noisy: it catches `268/26` (the intermediate surface nobody remembers is retired) as well
as `257/26`, and it catches the bare `26 domains` phrasing that survives when someone
updates the tool count and forgets the domain count.

---

## 11. What changed in this commit

| File | Change |
|---|---|
| `docs/pricing/tier-sensitivity.md` | **New.** This note. |
| `docs/pricing/tier_sensitivity_model.py` | **New.** Executable model; every figure above is printed by it, and it writes the CSV. |
| `docs/pricing/tier-sensitivity.csv` | **New.** Model output: the wedge table, the reachable and nearest-exact mixes, and the price band. |
| `docs/pricing/audit_acv_consistency.py` | **Extended.** Now also gates the retired tool surface: a line stating 257/268 tools or 26 domains in canonical `docs/` fails the build, unless it carries a retirement marker. `--no-surface` scopes back to the ACV invariant alone. |

No number outside `docs/pricing/` was modified. The $14,000 / $1.68M / TAM / SAM house
figures are carried verbatim.

To scope the gate to the ACV invariant alone while the 15 pre-existing lines are being
cleaned up by their owners, run with `--no-surface`.

---

**Carried verbatim:** blended ACV $14,000 · TAM $1.28B / SAM $282M / SOM $1.68M ·
tool surface 270/27 (257/26 retired) · COGS $4,280/account.
