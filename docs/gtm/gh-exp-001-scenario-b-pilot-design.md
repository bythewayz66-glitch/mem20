# GH-EXP-001 / Scenario B Pilot Design

**Date:** 2026-11-16  
**Status:** Design (ready for operator review)  
**Related:** `docs/gtm/experiment-gh-exp-001-prove-it-hero.md` (PR #416), GH-EXP-001

## Objective
Run a focused Scenario B pilot to test whether the "prove it" hero/auditability narrative improves qualified conversion quality, measured primarily by **tier migration** (upgrade movement from entry/self-serve intent to a higher-value tier) rather than raw traffic alone.

## Target list (pilot)
Use a small, manually curated list to preserve signal quality over volume.

| Segment | Target count | Source/identification | Why included | Primary contact motion |
|---|---:|---|---|---|
| Existing OSS evaluators with repeated repo activity | 15 | GitHub traffic/referrer proxies where available, stars/forks/watchers, issue/discussion participants, inbound repo contacts | Already aware of mem20; can evaluate auditability claim quickly | Direct outreach + guided evaluation |
| Agent-platform teams with compliance/audit needs | 10 | Known prospects/users asking for provenance, grounded memory, audit trails, or safety controls | Highest fit for grounded-vs-simulated wedge | Problem-fit call + demo |
| Current low-tier / self-serve users (if identifiable) | 10 | Internal account/support/install records where available; otherwise qualified inbound leads tagged "starter" | Directly eligible for tier migration measurement | Upgrade conversation with measured use case |
| Design partners / friendly reviewers | 5 | Trusted engineering or integrity-review contacts | Fast qualitative feedback and instrumentation validation | Structured pilot session |

**Total target:** 40 accounts/contacts (minimum viable: 25 if data access is limited).

### Qualification criteria
- Has an agent workflow where memory correctness/auditability matters.
- Can evaluate within 90 days (or provide a clear proxy decision).
- Willing to share enough outcome data for tier-migration/read-out metrics (even if anonymized/aggregated).

## Tier-migration metric (primary)
**Definition:** A qualified account moves to a higher commercial tier or a higher-intent paid evaluation state attributable to the Scenario B pilot.

### Proposed metric ladder (use highest observable level)
1. **Tier migration (hard):** Starter/entry -> Team/Business (or equivalent paid upgrade) within 90 days.
2. **Migration intent (soft proxy):** documented request/approval to upgrade tier, procurement/security review started, or signed pilot expansion agreement.
3. **Packaging migration (behavioral proxy):** adoption of features/capabilities gated to higher tier (if/when instrumented) plus explicit upgrade intent.

### Calculation
- **Migration rate** = migrated accounts / qualified pilot accounts exposed to Scenario B.
- **Net migration lift** (if control available) = Scenario B migration rate − baseline/control migration rate.
- **Time-to-migration** = median days from first Scenario B touch to migration event.

### Guardrails
- Exclude accounts already in active upgrade cycles before first Scenario B touch.
- Record attribution confidence (`high/medium/low`) per migration event.
- Do not count traffic-only engagement as migration.

## 90-day read-out plan

| Window | Activities | Outputs / decisions |
|---|---|---|
| Days 0–7 (setup) | Finalize target list, confirm eligibility, baseline current tier/state, ensure messaging + instrumentation fields exist | Pilot roster, baseline snapshot, tracking template live |
| Days 8–30 (exposure + activation) | Deliver Scenario B narrative/demo to targets; capture qualitative objections; monitor activation signals | Exposure log, early objections/themes, first migration-intent signals |
| Days 31–60 (conversion) | Follow-up on qualified accounts, address auditability/proof questions, collect evidence for migration decisions | Midpoint read-out: migration-intent count, blocked reasons, attribution notes |
| Days 61–90 (read-out) | Close loop on decisions, validate migration events, compare against baseline/control where possible | Final pilot report with migration rate, time-to-migration, confidence, and go/no-go recommendation |

### 90-day read-out deliverables
- Pilot roster with final disposition per account (migrated / intent / no change / disqualified / unknown).
- Tier-migration metric summary (hard + proxy) with attribution confidence.
- Top objections and evidence gaps preventing migration.
- Recommendation: scale, iterate narrative/packaging, or stop (with reasons).

## Risks / limitations
- Small sample sizes limit statistical confidence; treat as directional pilot evidence.
- Tier-migration attribution may be ambiguous without CRM/billing instrumentation; require explicit attribution notes.
- If no formal tiers are live in-product, proxy migration metrics must be clearly labeled as proxies.
