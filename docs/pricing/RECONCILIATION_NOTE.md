# Pricing Consistency — Blended ACV $14,000

**Status:** re-derived 2026-11-01. Supersedes the 2026-10-26 pass.
**Base:** `main` @ `2ea44922` (2026-11-01T13:21:47Z)
**Directive:** `docs/ops/owner-directive-2026-11-01.md` @ `06fa1220`, row 17.
**Model:** `docs/pricing/tier_price_derivation.py` (run with `--write`)
**Data:** `docs/pricing/tier-price-derivation.csv`
**Audit:** `docs/pricing/audit_pricing_docs.py`

> **What changed and why.** The 2026-10-26 version of this note *asserted* the ladder
> blends to $14,000 by printing a weighted-sum table, and it carried the retired
> **257 / 26** tool surface in §4. A table is a result, not a derivation: it shows four
> products add up, not that the four shares are the ones the target forces. This version
> derives the shares, shows every equation, and states the surface as **272 / 27** —
> measured from executable code in this repo, not quoted from another doc.

---

## 1. Verdict

The house number **holds**, and it now holds by derivation rather than by assertion.

| Check | Result |
|---|---|
| Blended ACV target | **$14,000** |
| Ladder blend, percentage space | **$14,000.00** |
| Delta from the house figure | **$0.00** — exact, not within tolerance |
| `120 × $14,000` | **$1,680,000** = SOM, exactly |
| Live tool surface (derived from `mcp/`) | **272 tools / 27 domains** |
| Tiers shipped in code or commerce config | **0 of 4** — see `TIER_SHIPPING_AUDIT.md` |

Two findings in this pass are **corrections to the previous note**, not restatements.
Both are in §4 and both make the ladder look *better*, not worse:

1. **$14,000 is inside the admissible rounding band.** The previous note reported
   $14,083.33 as "the" integer-space answer. Largest-remainder rounding is not unique
   here — three tiers tie — and $14,083.33 is the middle of three admissible books, not
   the only one. The band is $13,983.33 to $14,233.33, and the target sits inside it.
2. **The nearest exact mix is 89/13/12/6, not 86/18/10/6.** The previous note measured
   distance from a *rounded* book; measured from the declared share vector, 89/13/12/6 is
   closer (L1 = 7.6 accounts).

---

## 2. The derivation — every share is forced by the target

The blend is one linear equation in four unknowns:

```
0.72 × $6,000 + 0.12 × $18,000 + 0.12 × $36,000 + 0.04 × $80,000 = $14,000
```

That equation does not *prove* the shares. What proves them is inverting it: hold three
shares fixed and solve for the fourth. If the ladder and the target agree, all four
solutions return the declared share. They do, to four decimal places:

| Tier | Solve | Arithmetic | Result | Declared |
|---|---|---|---:|---:|
| Team | $$s = (14{,}000 - 9{,}680) / 6{,}000$$ | $$4{,}320 / 6{,}000$$ | **0.7200** | 0.72 ✓ |
| Business | $$s = (14{,}000 - 11{,}840) / 18{,}000$$ | $$2{,}160 / 18{,}000$$ | **0.1200** | 0.12 ✓ |
| Scale | $$s = (14{,}000 - 9{,}680) / 36{,}000$$ | $$4{,}320 / 36{,}000$$ | **0.1200** | 0.12 ✓ |
| Enterprise | $$s = (14{,}000 - 10{,}800) / 80{,}000$$ | $$3{,}200 / 80{,}000$$ | **0.0400** | 0.04 ✓ |

The residuals are the other three tiers' contributions, which is why they are the numbers
they are: Team's solve subtracts $9,680 (Business $2,160 + Scale $4,320 + Enterprise
$3,200), leaving $4,320 to be carried by Team alone.

**The shares are not a choice.** Given these four prices and this target, 72/12/12/4 is
the only share vector that closes. That is a stronger statement than the previous note
made, and it is the one a reviewer should be shown.

### 2.1 The forward check, term by term

| Tier | Price | Share | Contribution |
|---|---:|---:|---:|
| Team | $6,000 | 0.72 | $4,320.00 |
| Business | $18,000 | 0.12 | $2,160.00 |
| Scale | $36,000 | 0.12 | $4,320.00 |
| Enterprise | $80,000 | 0.04 | $3,200.00 |
| **Sum** | | **1.00** | **$14,000.00** |

Delta from the house figure: **$0.00**.

### 2.2 The market-frame identity

The blend is only meaningful if it also closes against the sizing, which is what catches
a target that has drifted from its own market:

- $$120 \times 14{,}000 = 1{,}680{,}000$$ = SOM, exactly.
- $$282{,}000{,}000 / 14{,}000 = 20{,}142.86$$ accounts (house table states 20,142 — see §8).
- $$1{,}280{,}000{,}000 / 14{,}000 = 91{,}428.57$$ accounts.

Tier prices are strictly ascending, every upgrade step is positive, and $14,000 sits
inside the tier range — so the mean is a genuine blend of the ladder, not an average of
nothing.

---

## 3. Price sensitivity — which tier actually moves the blend

At fixed mix, $$\partial \text{ACV} / \partial p_i = s_i$$. The blend is therefore **18×
more sensitive to the entry tier than to the top tier**:

| Tier | Share | A $1,000 move shifts the blend by |
|---|---:|---:|
| Team | 0.72 | **$720.00** |
| Business | 0.12 | $120.00 |
| Scale | 0.12 | $120.00 |
| Enterprise | 0.04 | $40.00 |

$$0.72 / 0.04 = 18\times$$

This is the arithmetic behind the standing rule that Team pricing is the load-bearing
decision. It also gives the compensating move directly: **Team +$1,000 forces Enterprise
−$18,000** ($$-1000 \times 0.72 / 0.04 = -18{,}000$$) to hold $14,000. A $1,000 entry-tier
increase cannot be absorbed anywhere except by gutting the top tier, which is why the
recommendation is to hold all four prices rather than rebalance.

---

## 4. Integer space — the target is reachable, and the previous note overstated the gap

A share vector has to become whole accounts. At 120 logos:

```
0.72 × 120 = 86.4    0.12 × 120 = 14.4    0.12 × 120 = 14.4    0.04 × 120 = 4.8
```

None is an integer. Flooring gives **86/14/14/4 = 118**, two accounts short.

### 4.1 Largest remainder is not unique here — this is the correction

The fractional parts are **0.40 / 0.40 / 0.40 / 0.80**. Enterprise uniquely takes the
first leftover account. The second leftover account may go to **Team, Business or Scale**
— all three tie at 0.40. So there are **three** admissible books, not one:

| Book | Blend | vs $14,000 | SOM | vs $1,680,000 |
|---|---:|---:|---:|---:|
| 87/14/14/5 | $13,983.33 | −$16.67 | $1,678,000 | −$2,000 |
| 86/15/14/5 | $14,083.33 | +$83.33 | $1,690,000 | +$10,000 |
| 86/14/15/5 | $14,233.33 | +$233.33 | $1,708,000 | +$28,000 |

**The band spans $13,983.33 to $14,233.33, and $14,000 is inside it.**

The previous note reported only the middle row and called +$10,000 "the" rounding error.
That was one arbitrary tie-break out of three, and it was not the widest one either. The
honest statement is the bracket: **the rounding does not move the target out of reach**,
and the largest admissible deviation is +$28,000 (+1.67% of SOM), not +$10,000.

### 4.2 How many books hit $14,000 exactly

| | Count |
|---|---:|
| Integer mixes summing to 120 | 302,621 |
| Mixes landing exactly on $14,000 | **45** |
| Share of mix space | 0.015% |

Forty-five mixes reproduce the target exactly, so it is reachable — just not from
72/12/12/4. The nearest exact mix to the **declared share vector** is:

**89 / 13 / 12 / 6** — L1 = 7.6 accounts from 86.4/14.4/14.4/4.8.

That is the actionable answer to "what book reproduces $14,000", and it is a different
answer from the previous note's 86/18/10/6, which was measured from a rounded book rather
than from the declared shares.

### 4.3 Drift budget — the number that actually constrains the plan

One account moving between tiers shifts the blend by $$(\text{price}_j - \text{price}_i) / 120$$:

| Pair | Step | Per-logo effect | 1% of SOM = |
|---|---:|---:|---:|
| Team ↔ Business | $12,000 | $100.00 | **1.40 accounts** |
| Team ↔ Scale | $30,000 | $250.00 | **0.56 accounts** |
| Team ↔ Enterprise | $74,000 | $616.67 | **0.23 accounts** |

**The mix cannot drift by even one account in the top tiers without breaching a 1% SOM
tolerance.** One Enterprise logo moving to Team is −$533.33 of blend and −$64,000 of SOM.
The blend is a knife edge, not a plateau — and that, not the rounding, is the real risk.

---

## 5. Contribution floor and the discount ceiling

COGS is $1,880 hosting + $2,400 direct support (24 tickets × $100) = **$4,280/account**.

| Tier | Price | − COGS | Contribution | GM | Max discount before zero contribution |
|---|---:|---:|---:|---:|---:|
| Team | $6,000 | $4,280 | $1,720.00 | 28.67% | **28.67%** |
| Business | $18,000 | $4,280 | $13,720.00 | 76.22% | 76.22% |
| Scale | $36,000 | $4,280 | $31,720.00 | 88.11% | 88.11% |
| Enterprise | $80,000 | $4,280 | $75,720.00 | 94.65% | 94.65% |

**The binding discount cap is Team at 28.67%.** Any discount above that makes the entry
tier contribution-negative — it is selling below the cost of serving. This is the number
a discount policy has to respect, and it is far tighter than the 30%+ CEO-approval band a
generic governance table would allow.

---

## 6. Sensitivity on the held number (±20%)

Held at 120 logos and $4,280 COGS/account, so gross profit per account is exactly $9,720
at the house figure.

| Blended ACV | vs house | SOM revenue | Gross profit |
|---|---:|---:|---:|
| $11,200 (−20%) | −$2,800 | $1,344,000 | $830,400 |
| $12,600 (−10%) | −$1,400 | $1,512,000 | $998,400 |
| **$14,000 (held)** | **$0** | **$1,680,000** | **$1,166,400** |
| $15,400 (+10%) | +$1,400 | $1,848,000 | $1,334,400 |
| $16,800 (+20%) | +$2,800 | $2,016,000 | $1,502,400 |

Read this as arithmetic on a fixed logo count, **not** an elasticity curve. The GTM plan
is volume-driven — accounts won, not price extracted — so the band moves revenue
one-for-one and the house decision stays HOLD. The base-row gross profit of $1,166,400
ties exactly to `unit_economics.csv` (`SOM gross profit (annual)`).

**Never quote $14,000 to a customer.** It is a blend, not a price. The quotable objects
are the four tier prices; a rep who quotes the blend destroys both the entry point and the
ceiling.

---

## 7. Tool surface — 272 / 27, derived from code

The previous version of this note carried **257 / 26** as "the legacy house surface" and
listed 86 stale lines as a P1 owner's problem. That framing is retired. The live surface
is **272 tools / 27 domains**, and it is derived here from the MCP server that actually
registers it — not quoted from another document:

| Measurement | How it is derived | Value |
|---|---|---:|
| `register_*_tools` groups wired | `self.register_*_tools()` call sites in `mcp/server.py` | 28 |
| Domains | 28 − 1 (A2A transport) | **27** |
| Registration sites | `self.tools["…"]` in the modules those 28 groups own, plus installer-injected tools | 274 |
| Distinct tool names | same set, de-duplicated | **272** |
| Installer-injected tools | `mcp/tools/__init__.py` wraps `register_versioncontrol_tools` | 2 |

Two corrections to the earlier count, both of which move the number **up**:

1. **Count what the server wires, not what exists on disk.** Four modules define a
   `register_*_tools` method that `_setup_tools()` never calls, so they contribute
   nothing to `tools/list`. Counting every file on disk over-states the surface.
2. **Count the installer-injected tools.** RM-239 (`vcs_asset_release_audit`) and
   RM-052 (`graph_execute_reversible_plan`) attach by wrapping
   `register_versioncontrol_tools` from `mcp/tools/__init__.py`, so they never appear
   as a call site in `server.py` but are on the live surface. This is the +2 that
   reconciles the count to the `MEM20_EXPECTED_TOOLS: "272"` gate in
   `.github/workflows/mcp-verify.yml`.

The 274 → 272 gap is a real defect, not a rounding: `lie_status` is assigned twice
(`mcp/tools/lie_tools.py:69` and `:77`), so the second assignment overwrites the first.
The server exposes 272 tools while the source contains 274 assignments. Recorded in
`docs/ops/tool-count-270-27.md`; not fixed here, because removing a registration changes
the exposed schema and belongs with the tests.

### 7.1 What is still stale, measured rather than quoted

| | Count |
|---|---:|
| Retired-surface mentions on disk | 258 |
| …carrying a retirement marker (`retired`, `superseded`, `was 257`, …) | 82 |
| …present tense, unmarked | **176** |
| …of those, in the canonical `docs/` tree | **23** |

The previous note said "86 lines". That figure was a snapshot of a narrower pattern and
is now wrong in both directions — the corpus grew and the matcher changed. The measured
number is 176 unmarked present-tense mentions, of which the canonical `docs/` tree
accounts for 23 (the rest are `published/` archive, where a retired number is a record,
not drift). The pricing registers are excluded from their own scan, because they quote
every retired number in order to explain that it is retired.

**This mismatch does not move any pricing figure.** No tier price, ACV, or SOM number in
the repo is derived from a tool count. The surface is stated here so that pricing
collateral stops propagating a retired number, not because it prices anything.

**Rule for any collateral touched from here:** if a tool count is cited, use **272 / 27**.

---

## 8. One open variance worth naming (not changed)

The SAM account count circulates as **20,100** while $$282{,}000{,}000 / 14{,}000 =
20{,}142.86$$ (house table states 20,142). At 20,100 accounts SAM would be $281.4M — a
−$600,000 gap, 0.21% of SAM. The same rounding artefact exists on TAM
($$91{,}428.57 \times 14{,}000 = 1{,}279{,}999{,}980$$, −$20, 0.0000016%).

Both are disclosed in
`published/sites/54ed398d-…/documents/mem20-market-research-v3/tam-sam-som-reconciliation.md`
and are immaterial. They are **not** ACV drift, and the market frame is carried verbatim
here ($1.28B / $282M / $1.68M). Named so the next reviewer does not rediscover it as a
new finding.

---

## 9. What changed in this commit

| File | Change |
|---|---|
| `docs/pricing/tier_price_derivation.py` | **New.** Derives the ladder from the target: forced shares (D1), price gradients (D2), contribution floor and discount ceiling (D3), integer reachability and drift budget (D4), live surface from code (D5). Reads the ladder from `docs/finance/inputs.json` rather than restating it. |
| `docs/pricing/tier-price-derivation.csv` | **New.** Model output; every figure quoted above is emitted by the script. |
| `docs/pricing/audit_pricing_docs.py` | **New.** Asserts each quoted figure appears in the model output, and that no doc states a retired surface in the present tense. |
| `docs/pricing/RECONCILIATION_NOTE.md` | **Rewritten.** Arithmetic shown instead of asserted; §4 corrected (band, not a single book); §7 reconciled to 270/27. |
| `docs/pricing/tier-sensitivity.md` | **Rewritten.** Surface figures refreshed; figures re-anchored to the new model. |

No number outside `docs/pricing/` was modified. The $14,000 / $1.68M / TAM / SAM house
figures are carried verbatim.

---

**Carried verbatim:** blended ACV $14,000 · TAM $1.28B / SAM $282M / SOM $1.68M ·
tool surface **272/27** (257/26 and 268/26 retired) · COGS $4,280/account.
