# Pricing Surface Accuracy — Tier vs. Shipped

**Date:** 2026-10-31
**Base:** `main` @ `27c1e5fb78def1d34b9b8f572a66f1424b1b350e` (v3.1.0 cut)
**Branch:** `chore/pricing-surface-accuracy`
**Question:** for every tracked doc that states a price, tier, or ACV — does the repo
actually *ship* that tier, and does the ACV arithmetic hold against the blended $14,000?

**The standing $14,000 blended ACV is not changed by this document.** It is an invariant
here. Where the repo contradicts it, this note reports the contradiction and leaves the
headline alone.

---

## 1. Verdict

The repo has a **complete, internally-consistent pricing narrative and zero shipped
pricing surface.** All four documented tiers exist only in copy. The $14,000 blend
reconciles exactly in percentage space and nowhere else.

| Question | Answer |
|---|---|
| Tiers documented? | Yes — 4 tiers, stated across 7 tracked files |
| Tiers shipped (plan/entitlement in code or config)? | **No — 0 of 4** |
| Billing surface with a price set? | **No — 15 SKUs, 0 priced** |
| $14,000 blended ACV arithmetically holds? | **Yes in percentage space; no on a 120-logo book** |
| Tiers that exist only in copy? | **All four: Team, Business, Scale, Enterprise** |

The previous reconciliation (`docs/pricing/RECONCILIATION_NOTE.md`) is correct on the
narrow question it asked — *do the ACV figures read $14,000?* — and its answer of 44/44
stands. But that check is a within-copy text scan. It cannot see this failure, because a
tier which is never implemented still reads $14,000 perfectly. **ACV consistency is not
pricing-surface accuracy.**

---

## 2. The tier-vs-shipped table

This is the deliverable. `SHIPPED` means a machine-readable plan/entitlement carrying the
tier exists in **executable code or commerce config** — not in a financial model's input
file, and not in prose.

| Tier | Documented ACV | Declared share | Docs stating it | Shipped counterpart | Verdict |
|---|---:|---:|---:|---|---|
| Team | $6,000 | 72% | 5 | **none** | **copy only** |
| Business | $18,000 | 12% | 4 | **none** | **copy only** |
| Scale | $36,000 | 12% | 3 | **none** | **copy only** |
| Enterprise | $80,000 | 4% | 3 | **none** | **copy only** |

Where each tier is stated:

| Tier | Files |
|---|---|
| Team | `docs/app/deck/slides/slide_07.html`, `slide_12.html`, `docs/ops/workload-roster-2026-10-27.md`, `docs/pricing/RECONCILIATION_NOTE.md`, `docs/pricing/tier-sensitivity.md` |
| Business | `slide_07.html`, `workload-roster-2026-10-27.md`, `RECONCILIATION_NOTE.md`, `tier-sensitivity.md` |
| Scale | `slide_07.html`, `RECONCILIATION_NOTE.md`, `tier-sensitivity.md` |
| Enterprise | `slide_07.html`, `RECONCILIATION_NOTE.md`, `tier-sensitivity.md` |

### 2.1 What *does* exist, and why it is not a shipped tier

| Artifact | What it is | Why it does not count |
|---|---|---|
| `docs/finance/inputs.json` → `tiers[]` | The ladder as **model input** | An input file describes pricing; it entitles nobody to anything. Delete it and the product still sells identically — because it sells nothing. |
| `docs/pricing/tier_sensitivity_model.py` | The ladder re-declared as **analysis constants** | Same: a model asserts a price, it does not gate a customer. |
| `docs/pricing/audit_acv_consistency.py` → `TIERS` | The ladder **hardcoded in the audit script** | This is the important one — see §4. |
| `mem20shopz/mem20shopz/catalog.json` | The **only** commerce surface | 15 SKUs, **every `amount_cents` null and every `price_id` empty**. Its own header says prices are intentionally unset until a real Stripe Price exists. |
| `mem20mktz/src/mem20mktz/pricing.py` | AdaptivePricingBrain | Computes `cost × (1+margin)` per *bundle*. No tier names, no tier prices. |
| `mem20adaptz/mem20adaptz/pricing.py` | Elasticity fit | Fits a demand curve from observations. No tier names, no tier prices. |

The two `pricing.py` modules are the closest thing to a shipped pricing capability, and
**neither contains a single tier name or tier price.** They are generic price *engines*
(one cost-plus, one elasticity-fit). The repo ships the ability to compute a price and
ships none of the prices it documents.

### 2.2 The SKU names do not match the tiers either

This is a second, independent proof that the ladder is unshipped — not just that a lookup
failed. The catalog's 15 SKUs are a different product vocabulary entirely:

```
foundation-single   fleet-starter    hosting-monthly   ops-audit
control-plane-setup oncall-monthly   memory-tiering    agent-fleet-build
intelligence-monthly asset-pipeline  game-vertical     studio-monthly
migration           training         priority-support-monthly
```

Not one of them is `team`, `business`, `scale`, or `enterprise`. The shipped commerce
model is *à-la-carte services plus monthly add-ons*; the documented pricing model is a
*six-figure ACV tier ladder*. **These are two different businesses.** The one with prices
is the one nobody wrote a deck about.

---

## 3. Does the $14,000 arithmetic hold?

Held at 120 logos and COGS $4,280/account (the canonical stack).

### 3.1 Percentage space — passes exactly

| Tier | ACV | Share | Weighted |
|---|---:|---:|---:|
| Team | $6,000 | 72% | $4,320.00 |
| Business | $18,000 | 12% | $2,160.00 |
| Scale | $36,000 | 12% | $4,320.00 |
| Enterprise | $80,000 | 4% | $3,200.00 |
| **Blend** | | **100%** | **$14,000.00** |

Delta: **$0.00**, exact. The identity `120 × $14,000 = $1,680,000` also holds.

### 3.2 Integer space — fails by $83.33/logo

The declared shares are **not whole accounts** at 120 logos:

```
72% × 120 = 86.4    12% × 120 = 14.4    12% × 120 = 14.4    4% × 120 = 4.8
```

| Rounding | Mix | Sum | Blended ACV | vs $14,000 |
|---|---|---:|---:|---:|
| Naive `round()` per tier | 86/14/14/5 | **119** | — | silently loses an account |
| **Largest remainder** | **86/15/14/5** | **120** | **$14,083.33** | **+$83.33** |
| Read literally | 86.4/14.4/14.4/4.8 | 120 | $14,000.00 | not a book |

At the honest reachable mix:

| | Blended ACV | SOM revenue | GP/account | SOM gross profit |
|---|---:|---:|---:|---:|
| House figure | $14,000.00 | $1,680,000 | $9,720.00 | $1,166,400 |
| Reachable 86/15/14/5 | $14,083.33 | $1,690,000 | $9,803.33 | $1,176,400 |
| Delta | +$83.33 | **+$10,000 (+0.60%)** | +$83.33 | +$10,000 |

**Verdict on the arithmetic:** the ladder is a valid pricing *structure*, and `$14,000` is
a rounding convention applied to it — not an output of it. Independently verified: there
are exactly **45** integer mixes at 120 logos that hit $14,000 exactly; the nearest to the
declared mix is **86/18/10/6** (8 accounts of movement). The target is reachable, just not
from 72/12/12/4.

### 3.3 The drift budget is unusually thin

One account moving between tiers shifts the blend by `(price_to − price_from) / 120`:

| Movement | Blend shift | % of blend | Accounts to breach 1% |
|---|---:|---:|---:|
| Team → Business | +$100.00 | 0.71% | 1.40 |
| Team → Scale | +$250.00 | 1.79% | 0.56 |
| Team → Enterprise | +$616.67 | 4.40% | **0.23** |

**A single Enterprise account is worth more than four times the whole 1% tolerance.** At
that sensitivity the blend is not a forecast, it is a coincidence. This is the strongest
argument for treating $14,000 as a board convention to be held by fiat rather than a
derived number that survives contact with a pipeline.

---

## 4. Contradictions of the standing $14,000 — reported, not changed

### 4.1 `docs/gtm/mem20-sales-one-pager.md` documents a **different ladder**

This is the most consequential finding after the copy-only tiers. The sales one-pager
(§"Packaging") states a four-tier structure that shares **no tier name and no price** with
`docs/finance/inputs.json`. Worse, it makes the blended ACV itself a **quoted tier price**:

| One-pager tier | Price | Status |
|---|---:|---|
| Free / OSS | $0 | proposed |
| **Supported** | **$14,000/yr — "the blended ACV anchor"** | proposed |
| Compliance pack | $28,000–$42,000/yr | proposed |
| Platform | $56,000+/yr | proposed |

Two direct contradictions of the house model:

1. **It quotes the blend.** The document's own line above the table says *"no price list
   exists in the repo; these are GTM proposals, label them as such"* — good hygiene — but
   it immediately sets **$14,000/yr as an actual sellable tier price**. That converts the
   blend from a portfolio average into a customer-facing quote, which is exactly the
   failure mode the pricing discipline exists to prevent: a rep who quotes the blend
   destroys both the $6,000 entry point and the $80,000 ceiling.
2. **It cannot reproduce $14,000.** A blend of {0, 14,000, 35,000, 56,000} only equals
   $14,000 if **100% of logos sit in Supported**. Any Compliance-pack or Platform customer
   pulls the blend *up*; any Free/OSS pulls it *down*. Concretely: a plausible mix of
   40 Free / 40 Supported / 25 Compliance / 15 Platform over 120 logos blends to
   **$18,958.33** — **+$4,958 (+35.4%)** above the house figure, with no pricing decision
   having been made, only a plausible mix. The ladder has no mix that lands on the house
   figure while leaving room for its own upper tiers.

Nothing here is corrected — the standing figure is the business's to hold. But the
one-pager and the finance model are describing two incompatible price books, and only one
of them is the documented house ladder.

### 4.2 The audit script hardcodes the ladder instead of reading it

`docs/pricing/audit_acv_consistency.py:24` declares its own copy:

```python
TIERS = [("Team", 6_000, 72), ("Business", 18_000, 12),
         ("Scale", 36_000, 12), ("Enterprise", 80_000, 4)]
```

`docs/finance/inputs.json` also declares the ladder. The invariant is therefore only
guaranteed **against itself** — repricing the model in `inputs.json` would leave the audit
green, because the audit never reads `inputs.json`. A guard that duplicates its own subject
cannot detect drift in it. This is a correctness defect in the enforcement, not in the
figure.

### 4.3 One documented figure is stale by three releases

`docs/pricing/tier-sensitivity.md` cites `$14,000` throughout (correct) but its
`docs/ops/workload-roster-2026-10-27.md:68` assignment line still describes the ladder as
`unvalidated` — which the tier-sensitivity note then resolved. The roster is a planning
record, so this is inert, but it is why a reviewer arriving fresh reads "unvalidated" in
one file and a completed analysis in another.

---

## 5. Sensitivity of the held number (±20%)

Held at 120 logos, COGS $4,280/account, GP/account = ACV − $4,280.

| Blended ACV | vs house | SOM revenue | Gross profit | GP margin |
|---|---:|---:|---:|---:|
| $11,200 (−20%) | −$2,800 | $1,344,000 | $830,400 | 61.8% |
| $12,600 (−10%) | −$1,400 | $1,512,000 | $998,400 | 66.0% |
| **$14,000 (held)** | **$0** | **$1,680,000** | **$1,166,400** | **69.4%** |
| $15,400 (+10%) | +$1,400 | $1,848,000 | $1,334,400 | 72.2% |
| $16,800 (+20%) | +$2,800 | $2,016,000 | $1,502,400 | 74.4% |

Read as arithmetic on a fixed logo count, **not** an elasticity curve: the GTM plan is
volume-driven (accounts won, not price extracted), so the band moves revenue one-for-one.
Decision stays **HOLD**. The $1,166,400 base row ties exactly to `unit_economics.csv`
(`SOM gross profit (annual)`).

---

## 6. What this means for the repo

The gap is not that the numbers are wrong. It is that **there is no product to attach them
to.** A deck, a sales one-pager, a finance model, a tier-sensitivity study and a
reconciliation note all describe a priced product; the catalogue that would bill for it has
15 unpriced SKUs under unrelated names.

Two internally consistent ways to close it — the business must pick, and this note does not
pick for them:

| Option | What changes | What it costs |
|---|---|---|
| **Ship the ladder** | Map `team/business/scale/enterprise` onto 4 catalog SKUs with real Stripe `price_id` + `amount_cents`. Keep the ladder exactly as documented. | Requires 4 real prices to exist in Stripe — the blocking dependency the catalog comment already names. |
| **Retire the ladder** | Downgrade all four tiers to explicitly-labelled *proposals* everywhere (deck, one-pager, finance model), and let the à-la-carte catalog be the price book. | The $14,000 blend then has no ladder underneath it and must be re-derived or declared a target. |

The one thing that cannot continue is the current state: **a tier ladder published as if
shipped, with no shipped counterpart anywhere in the repo.**

---

## 7. Machine-checkable guard

`docs/pricing/audit_tier_shipping.py` (new in this branch) encodes everything above and
exits 1 on the finding.

```
$ python3 docs/pricing/audit_tier_shipping.py
  Tier               ACV  docs  shipped (plan/entitlement in code or config)
  Team        $    6,000     5  *** NONE - copy only ***
  Business    $   18,000     4  *** NONE - copy only ***
  Scale       $   36,000     3  *** NONE - copy only ***
  Enterprise  $   80,000     3  *** NONE - copy only ***

== Commerce surface ==
  mem20shopz/mem20shopz/catalog.json: 15 SKUs, 0 with an amount set

== Ladder arithmetic against the $14,000 house figure ==
  percentage-space blend  : $14,000.00  (delta $+0.00)
  largest-remainder mix   : [86, 15, 14, 5]  sum=120
  integer-space blend     : $14,083.33  (delta $+83.33)
  integer-space SOM       : $1,690,000  (delta $+10,000)
  exact mixes at 120 logos: 45; nearest [86, 18, 10, 6]

FINDING: copy-only tiers (documented, never shipped): Team, Business, Scale, Enterprise
$ echo $?
1
```

### 7.1 Matcher precision

The first draft of this scan produced false positives, which is worth recording because
they are the two traps any future scan will hit:

| False positive | Why it fired | Fix |
|---|---|---|
| `mcp/tools/blender_tools.py` matched "Scale" | `"scale": [x, y, z]` — a geometry param, on a line that also contains the word "tier" | require the tier name to be a **quoted string literal** |
| `mem20core/mem20core/core.py` matched "Team" | `incident_team` — an agent list | same |
| `mcp/tools/finance_tools.py`, `web/src/data/tools.json` matched "Business"/"Scale" | "Track personal or business expenses", blender `"scale"`, inside a minified 270-tool JSON dump | require a gating keyword within **±60 chars** of the literal |

The matcher is verified both ways: a genuine `PLANS = {"team": {...}, "enterprise": {...}}`
structure **is** detected, and the three false-positive strings above are **not**.

### 7.2 Relationship to the existing audit

| Script | Asks | Result today |
|---|---|---|
| `audit_acv_consistency.py` | Do the ACV figures read $14,000? | Exit 1 — but only on retired **tool-count** strings (257/26, 268/26), which are pre-existing and unrelated to ACV. ACV itself is clean. |
| **`audit_tier_shipping.py`** (new) | Does each documented tier have a shipped counterpart, and does the ladder reconcile on a real book? | **Exit 1 — copy-only tiers.** |

Both exit 1 today, for unrelated reasons. The ACV text scan is green on ACV; the surface
scan is red on tiers.

---

## 8. Scope and method

- Base commit: `27c1e5fb78def1d34b9b8f572a66f1424b1b350e` (v3.1.0). `main` has since moved
  two infra commits ahead (`f167247`, `de37968`). `git diff --stat` across
  `docs/pricing docs/finance docs/gtm mem20shopz` for that range is **empty** — no pricing
  drift was introduced by the intervening commits, so findings are valid at both.
- Scanned: all tracked files, excluding `.git`, `published/sites/*` (rendered duplicates of
  already-counted source docs) and `mem20orcaz/*` (a vendored benchmark corpus whose
  `$6,000`/`$80,000` hits are dataset scores, not prices).
- Ship roots probed: `mcp`, `gateway`, `mem20api`, `mem20core`, `mem20corez`, `mem20shopz`,
  `mem20biz`, `web/src`, `packaging`.
- Deliberately **not** counted as shipping: `docs/finance`, `docs/pricing` — model inputs
  and analysis are documents about pricing, not plans.
- Every figure in this note is emitted by `audit_tier_shipping.py`; none was hand-transcribed.

**Carried verbatim:** blended ACV **$14,000** · TAM **$1.28B** / SAM **$282M** / SOM
**$1.68M** · 120 logos · COGS **$4,280**/account.
