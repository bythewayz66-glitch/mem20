# mem20 — TAM / SAM / SOM Reconciliation (v3, rev 2026-10-18)

House numbers are held constant and are NOT re-derived here: TAM $1.28B / SAM $282M / SOM $1.68M, blended ACV $14,000.
This file tests whether the house numbers survive independent arithmetic. Where they do not reconcile exactly, the residual is disclosed rather than smoothed.

## 1. Top-down anchor (why $1.28B and not $6.49B)

| Step | Value | Derivation |
|---|---|---|
| Broad category (TBRC, "Agentic AI Orchestration and Memory Systems", 2025) | $6,490,000,000 | published report figure |
| Auditable slice as % of broad category | 19.72% | 1,280,000,000 / 6,490,000,000 = 0.197227 |
| **TAM (house)** | **$1,280,000,000** | global auditable agent-memory slice |

Cross-check of the broad base against independent houses: Mordor puts the same category at $6.27B (2025) and SkyQuest at $6.16B (2025). The house $6.49B is therefore at the top of the published band — defensible, but it is the aggressive end, which is exactly why mem20 quotes the *slice* rather than the broad figure.

The auditable slice is defined as memory / vector-store + observability + governance / audit-trail components sold to enterprises carrying mandatory AI record-keeping obligations: EU AI Act Art. 12 (high-risk obligations, enforceable 2 Aug 2026), SEC/FINRA, HIPAA, SOX, ISO/IEC 42001, NIST AI RMF.

## 2. Bottom-up cross-checks at $14,000 blended ACV

| Layer | Accounts | Arithmetic | Value | House figure | Delta |
|---|---|---|---|---|---|
| TAM | 91,429 | 91,429 × 14,000 | $1,280,006,000 | $1,280,000,000 | **+$6,000** (+0.0005%) |
| SAM | 20,100 | 20,100 × 14,000 | $281,400,000 | $282,000,000 | **−$600,000** (−0.21%) |
| SOM | 120 | 120 × 14,000 | $1,680,000 | $1,680,000 | **$0 (exact)** |

Ratios: SAM / TAM = 22.03% (20,100 / 91,429 = 21.98% by account count). SOM / SAM = 0.596%. SOM / TAM = 0.131%.

## 3. Residual disclosure (required reading)

The three layers do NOT sum to a zero residual. Total residual across the three rows is **−$594,000**.

- The **TAM** row is a rounding artefact only: $1.28B / $14,000 = 91,428.57 accounts, so 91,429 accounts overshoots by $6,000. Immaterial at 0.0005%.
- The **SOM** row is exact by construction: 120 × 14,000 = 1,680,000.
- The **SAM** row is the one real gap: the house figure $282M implies 20,142.86 accounts, not the 20,100 account count that circulates with it. At 20,100 accounts the figure is $281.4M, a −$600,000 gap (0.21% of SAM).

**How to quote this without creating a fourth number set:** treat $282M as the house SAM and treat 20,100 as an *approximately* 20,100-account build of it. Do not add, subtract or re-derive SAM from the account count in any downstream asset. If an asset needs exact arithmetic, quote the SOM ($1.68M = 120 × $14,000), which is exact.

## 4. What would break the house numbers

1. Any asset quoting the broad $6.49B as mem20's TAM. The canonical position is the $1.28B slice.
2. Any ACV other than $14,000 blended, until the owner signs off otherwise.
3. Any SAM stated as an exact account multiple of $14,000. It is a ~20,100-account build, not an exact one.
4. Re-deriving TAM from account counts without the top-down anchor: the bottom-up alone cannot distinguish $1.28B from $1.29B.

## 5. Scenario sensitivity (not house numbers — clearly labelled illustrative)

Revenue is flat under ACV sensitivity because the GTM plan is volume-driven (accounts won), not price-driven. Holding SOM at 120 accounts:

| Blended ACV | SOM revenue | vs house |
|---|---|---|
| $12,000 | $1,440,000 | −$240,000 |
| **$14,000 (house)** | **$1,680,000** | **baseline** |
| $16,000 | $1,920,000 | +$240,000 |

The decision this implies stays where the Orchestrator left it: HOLD $14,000 blended ACV; sensitivity is flat on volume.
