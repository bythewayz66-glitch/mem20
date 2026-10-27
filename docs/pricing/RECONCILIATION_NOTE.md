# Pricing Consistency — Blended ACV $14,000

**Status:** reconciled and verified. No collateral required a numeric change.
**Date:** 2026-10-26
**Scope:** `docs/`, `published/`, and every pricing/tier table in the repo.

---

## 1. Verdict

The house number **holds**: blended ACV **$14,000**.

| Check | Result |
|---|---|
| Files scanned for ACV claims | 2,011 |
| ACV figures found | 44 |
| Figures equal to $14,000 | **44** |
| Figures disagreeing with $14,000 | **0** |

**There is no ACV drift in the repo.** Every one of the 44 ACV figures — across
`README.md`, `CHANGELOG.md`, the daily reports, the market-research-v3 set (MD + both
HTML renders + `gabe-bundle`), the finance report and its CloudDoc leg, the packaging
docs, the UX research set, the launch copy and all `mem20-launch` renders, the
status page and the prototype — states $14,000. Nothing was rewritten because nothing
disagreed.

This is a verified negative result, not an absence of checking. The harness that
produces it is `docs/pricing/audit_acv_consistency.py` (run:
`python3 docs/pricing/audit_acv_consistency.py -v`); it exits non-zero the moment any
figure drifts, so the invariant is now enforceable in CI rather than asserted in prose.

Three apparent disagreements were investigated and are **not** ACV drift, and were
correctly left alone:

| Apparent mismatch | What it actually is |
|---|---|
| `$8,000` / `$16,800` | Blended **CAC**, not ACV. Documented as a CAC pair (benchmark vs canonical repo state) in the finance report. |
| `$1,680,000` | **SOM**, the result of `120 × $14,000`. An arithmetic chain, not a competing ACV. |
| `$6,000 / $18,000 / $36,000 / $80,000` | **Tier-level** ACVs on the ladder. Per-segment prices, never blended claims. |

The audit script encodes exactly these three exclusions, so it does not re-litigate
them on every run.

## 2. The ladder reproduces the house number exactly

| Tier | ACV | Share of paying accounts | Weighted contribution |
|---|---:|---:|---:|
| Team | $6,000 | 72% | $432,000 |
| Business | $18,000 | 12% | $216,000 |
| Scale | $36,000 | 12% | $432,000 |
| Enterprise | $80,000 | 4% | $320,000 |
| **Blended** | — | **100%** | **$1,400,000 / 100 = $14,000** |

Delta from the house figure: **$0.00**, exact — not within tolerance.

The identity also holds against the market frame, which is what actually catches a
target that has drifted from its own sizing:

- `120 logos × $14,000 = $1,680,000` = SOM, exactly.
- `SAM $282M ÷ $14,000 ≈ 20,143` accounts (house table states 20,142 — see §5).
- `TAM $1.28B ÷ $14,000 ≈ 91,429` accounts.

Tier prices are strictly ascending, each upgrade step is positive, and $14,000 sits
inside the tier range — so the mean is a genuine blend of the ladder, not an average of
nothing.

## 3. Sensitivity on the held number (±20%)

Held at 120 logos and the canonical cost stack ($4,280 COGS/account: $1,880 hosting +
$2,400 direct support), so gross profit per account is exactly $9,720.

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
ties exactly to `unit_economics.csv` (`SOM gross profit (annual)`), which is the
doc-to-model check that catches rounding drift.

**Never quote $14,000 to a customer.** It is a blend, not a price. The quotable objects
are the four tier prices above; a rep who quotes the blend destroys both the entry point
and the ceiling.

## 4. Stale references flagged — NOT fixed (owned by Webpage Developer, P1)

The legacy house tool surface is **257 tools / 26 domains**. It is being superseded to
**270 / 27** by the P1 owner. Per that ownership, these references are **flagged here and
left untouched** — correcting them is the P1 slice, not this one:

| Location | What is stale |
|---|---|
| `published/sites/aca25e94-…/documents/mem20-finance-pricing-publish/compute_model.py:41-42` | `"tools": 257`, `"domains": 26` in `CANONICAL_REPO` |
| same file, `:434` (row `C-10`) | tolerance band `"257-260"` — **270 falls outside it**, so the model's own declared band no longer contains the live surface |
| same file, `:436` (row `C-11`) | `"Domains": "26"` |
| `published/daily-reports/2026-10-24.md`, `2026-10-25.md`, `2026-10-26.md` | `257 tools · 26 domains` in the standing positioning line (8 lines total) |
| `published/README.md` | `257 tools across 26 domains` |
| `published/sites/e1381e73-…/webpages/mem20-prototype/index.html` | 10 occurrences |
| `published/sites/538c6667-…/webpages/mem20-design-research/index.html` (+ `wireframes.html`) | 14 occurrences |
| `published/sites/54ed398d-…` market-research-v3 (MD, both HTML renders, `gabe-bundle`) | 10 occurrences |
| `published/sites/fb74dacb-…`, `f7c01331-…`, `dfe17c05-…`, `aac70cf5-…` (launch_v2/v3/v4) | 16 occurrences |
| `published/sites/60714d81-…/webpages/mem20-status-2026-10-14/index.html` | 4 occurrences |
| `published/sites/051e63be-…/webpages/mem20-ux-research-findings/index.html` | 4 occurrences |
| `published/sites/a590cfd2-…/documents/mem20-sdk-docs-publish-leg/*` | 7 occurrences |
| `docs/sdk/cpp/source-ledger.md` | 2 occurrences |

**86 lines total** match `257 tools` / `257/26`. Current state of the surface in the docs
tree is already 270/27 (`CHANGELOG.md`, `docs/README.md`, `docs/sdk/cpp/protocol.md`,
`mem20-sdk-ruby/`), so the repo currently states both numbers.

**Rule for any collateral touched from here:** if a tool count is cited, use **270 / 27**.
Never propagate 257/26 into new material. `CHANGELOG.md` already records the
reconciliation: the `memory_*` row listed 49 tools against 52 registered, and the 10
`lie_*` tools were absent from every table.

This mismatch does **not** move any pricing figure — no tier price, ACV, or SOM number in
the repo is derived from a tool count.

## 5. One open variance worth naming (not changed)

The SAM account count circulates as **20,100** while `$282M ÷ $14,000 = 20,143` (house
table states 20,142). At 20,100 accounts SAM would be $281.4M — a −$600,000 gap, 0.21% of
SAM. The same rounding artefact exists on TAM (91,429 accounts × $14,000 = $1,280,006,000,
+$6,000, 0.0005%). Both are already disclosed in
`published/sites/54ed398d-…/documents/mem20-market-research-v3/tam-sam-som-reconciliation.md`
and are immaterial; they are **not** ACV drift and the market frame is carried verbatim
here ($1.28B / $282M / $1.68M). Named so the next reviewer does not rediscover it as a
new finding.

## 6. What changed in this commit

| File | Change |
|---|---|
| `docs/pricing/audit_acv_consistency.py` | **New.** Machine-checkable ACV invariant: parses every ACV claim in the repo, fails on drift, and asserts the ladder blend + SOM identity + SAM/TAM cross-checks. |
| `docs/pricing/RECONCILIATION_NOTE.md` | **New.** This note. |

No file outside `docs/pricing/` was modified. No collateral number was rewritten, because
none disagreed with $14,000.

---

**Carried verbatim:** blended ACV $14,000 · TAM $1.28B / SAM $282M / SOM $1.68M ·
tool surface 270/27 (257/26 superseded, flagged above).
