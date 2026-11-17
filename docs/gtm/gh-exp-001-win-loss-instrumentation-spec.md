# GH-EXP-001 Win/Loss Instrumentation Spec

**Date:** 2026-11-16  
**Purpose:** Replace the assumed `−0.8` elasticity assumption with measured win/loss and price-sensitivity data.

## Goals
- Capture structured win/loss outcomes for opportunities exposed to the GH-EXP-001 / Scenario B narrative.
- Measure observed price sensitivity and tier-selection behavior from real decisions (not assumptions).
- Produce analyzable data for elasticity estimation with explicit confidence and caveats.

## Instrumentation principles
- **Privacy-respecting:** collect only business-necessary fields; no PII in free-text beyond contact role context where required; prefer anonymized/account IDs.
- **Evidence-first:** every outcome must include reason codes and attribution confidence.
- **Separation of concerns:** distinguish narrative exposure, product fit, pricing, and procurement blockers.
- **No fabricated metrics:** if a field is unknown, record `unknown` (never infer).

## Event taxonomy (minimum viable)

| Event | When emitted | Required fields | Notes |
|---|---|---|---|
| `opportunity_created` | Opportunity/account enters pilot or evaluated funnel | `opportunity_id`, `account_id_hash`, `created_at`, `segment`, `source`, `scenario_variant` (`control`/`treatment`/`scenario_b`/`unknown`) | Baseline record |
| `narrative_exposed` | Account receives GH-EXP-001 narrative/demo/material | `opportunity_id`, `exposed_at`, `exposure_type` (hero/demo/call/doc), `scenario_variant`, `owner` | Attribution anchor |
| `pricing_presented` | A price/tier/package is presented | `opportunity_id`, `presented_at`, `tier_presented`, `list_price`, `currency`, `discount_offered` (bool/amount), `billing_term` | Enables price-sensitivity analysis |
| `objection_recorded` | Meaningful objection captured | `opportunity_id`, `recorded_at`, `objection_category`, `objection_detail_code`, `severity`, `related_to` (`price`/`fit`/`trust`/`procurement`/`timing`/`other`) | Multiple allowed |
| `opportunity_outcome` | Final decision reached (or 90-day cutoff) | `opportunity_id`, `outcome_at`, `outcome` (`won`/`lost`/`no_decision`), `selected_tier`, `final_price`, `discount_final`, `competitor_or_alternative`, `primary_reason_code`, `secondary_reason_codes[]`, `attribution_confidence` | One terminal record per cycle |
| `tier_migration_observed` | Tier change/upgrade intent or upgrade completed | `opportunity_id`, `observed_at`, `from_tier`, `to_tier`, `migration_type` (`hard`/`intent`/`proxy`), `evidence_ref` | Links win/loss and pilot migration metric |

## Core fields and controlled vocabularies

### Outcome reason codes (primary/secondary)
- `price_too_high`
- `price_unclear`
- `value_not_proven`
- `missing_feature`
- `security_or_compliance_gap`
- `integration_cost_too_high`
- `chose_internal_build`
- `chose_competitor`
- `no_budget_timing`
- `no_decision_owner`
- `auditability_wedge_resonated` (win-positive)
- `other` (requires note)

### Attribution confidence
- `high`: direct evidence links exposure to outcome (documented decision path)
- `medium`: plausible linkage, incomplete evidence
- `low`: weak or ambiguous linkage

## Elasticity measurement plan (replacing −0.8 assumption)
The current `−0.8` elasticity is a placeholder assumption until measured.

### Data required
- Presented tier/price and final accepted/rejected price per opportunity.
- Outcome (won/lost/no decision) and primary reason codes.
- Variant exposure (`control`/`treatment`/`scenario_b`) to segment narrative effects.
- Time period and segment identifiers for normalization.

### Analysis approach
1. **Descriptive baseline:** win rate by tier, price band, discount band, and segment.
2. **Price-response estimation:** estimate demand/win probability sensitivity to price changes (e.g., logistic regression on win/loss with price and controls; or arc-elasticity on observed price bands where sample supports).
3. **Segmented read:** compute elasticity separately for audit-sensitive segments vs general segments if sample size permits.
4. **Uncertainty reporting:** report confidence intervals and minimum sample thresholds; suppress/label unstable estimates.
5. **Assumption replacement policy:** update pricing models only when measured estimate meets pre-defined data quality threshold (e.g., >= N qualified outcomes with adequate price variation); otherwise keep assumption explicitly labeled as provisional.

## Data quality and governance
- Required-field validation at capture time; reject terminal outcomes without `primary_reason_code`.
- Weekly audit for duplicates, missing outcomes, and inconsistent tier/price records.
- Store evidence references (doc/CRM note IDs) for `high` attribution claims.
- Keep a changelog for vocabulary updates to preserve longitudinal comparability.

## Reporting outputs (90-day)
- Win/loss summary by variant, segment, tier, and reason code.
- Measured price sensitivity / elasticity estimate (or "insufficient data" with gap analysis).
- Recommended pricing-model updates (if evidence threshold met) and remaining assumptions.
