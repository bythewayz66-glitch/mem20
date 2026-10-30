# UC-MEM-AV-GOV-001 — Government / High-Stakes Interview Support

**Status:** Implemented (mode + dual-control + seal metadata + hard gates)  
**Parent:** [UC-MEM-AV-001](./UC-MEM-AV-001.md)  
**Subsystem:** mem20liez (`mode="government"`)

## Goal

Same live behavioural pipeline under stricter consent, jurisdiction, dual-control, and audit rules.

## Requirements → implementation

| Requirement | Implementation |
|-------------|----------------|
| Explicit consent | `lie_start_session(..., consent=True, consent_attested_by=...)` required; re-checked at seal |
| Operator training | `lie_acknowledge_training` required before high-stakes start |
| Jurisdiction tag | Passed through; stored on sealed package meta |
| No automated decisions | Prohibited-use gate + contamination firewall |
| Dual control | `lie_dual_acknowledge(session_id, cue_id, first_officer_id, second_officer_id)` — two distinct IDs |
| Immutable seal | `lie_seal_session` → grounded memory + braid event + firewall block |
| Disclaimer | Always present on sealed package |

## Flow

1. `lie_acknowledge_training(operator_id, version="2026-10-30")`
2. `lie_start_session(mode="government", consent=true, consent_attested_by="...", jurisdiction="...", subject_id="...", operator_id="...")`
3. Optional `lie_set_baseline` with calm audio
4. Continuous `lie_feed_audio` / video frames via session API
5. `lie_get_cues` → earpiece; high-priority cues **must** use `lie_dual_acknowledge`
6. `lie_seal_session` → package with meta + disclaimer + dual-control records written to grounded store

## Prohibited

- Presenting scores as definitive proof of deception or intent
- Automatic detention / charge / clearance decisions
- Operating government mode without recorded consent or training
- Sealing while any high-priority cue lacks dual acknowledgement

## Acceptance

- [x] `mode=government` + consent enforcement
- [x] Dual-control tool with distinct-officer check
- [x] Seal carries jurisdiction / subject / consent / dual-control metadata
- [x] Braid + grounded write path on seal
- [x] Prohibited-use and contamination gates
- [x] Operator training gate
- [ ] Formal oversight export renderer (future)
- [ ] External legal review complete (see LEGAL-REVIEW-REQUEST.md)
