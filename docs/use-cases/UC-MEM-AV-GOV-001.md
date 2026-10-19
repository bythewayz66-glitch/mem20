# UC-MEM-AV-GOV-001 — Government / High-Stakes Interview Support

**Status:** Implemented (mode + dual-control + seal metadata)  
**Parent:** [UC-MEM-AV-001](./UC-MEM-AV-001.md)  
**Subsystem:** mem20liez (`mode="government"`)

## Goal

Same live behavioural pipeline under stricter consent, jurisdiction, dual-control, and audit rules.

## Requirements → implementation

| Requirement | Implementation |
|-------------|----------------|
| Explicit consent | `lie_start_session(..., consent=True)` required for government |
| Jurisdiction tag | Passed through; stored on sealed package meta |
| No automated decisions | Cues are advisory text only |
| Dual control | `lie_dual_acknowledge(session_id, cue_id, second_officer_id)` |
| Immutable seal | `lie_seal_session` → grounded memory + braid event |
| Disclaimer | Always present on sealed package |

## Flow

1. `lie_start_session(mode="government", consent=true, jurisdiction="...", subject_id="...")`
2. Optional `lie_set_baseline` with calm audio
3. Continuous `lie_feed_audio` / video frames via session API
4. `lie_get_cues` → earpiece; high-priority cues may use `lie_dual_acknowledge`
5. `lie_seal_session` → package with meta + disclaimer written to grounded store

## Prohibited

- Presenting scores as definitive proof of deception or intent
- Automatic detention / charge / clearance decisions
- Operating government mode without recorded consent

## Acceptance

- [x] `mode=government` + consent enforcement
- [x] Dual-control tool
- [x] Seal carries jurisdiction / subject / consent metadata
- [x] Braid + grounded write path on seal
- [ ] Formal oversight export renderer (future)
