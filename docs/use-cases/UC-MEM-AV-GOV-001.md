# UC-MEM-AV-GOV-001 — Government / High-Stakes Interview Support

**Status:** Proposed + initial implementation hooks  
**Parent:** UC-MEM-AV-001  
**Subsystem:** mem20liez (mode=`government`)

## Goal

Support government, intelligence, border, or other high-stakes interviews with the same live behavioural-signal pipeline, under stricter audit, consent, jurisdiction, and retention rules.

## Distinct Requirements

| Requirement | Detail |
|-------------|--------|
| Explicit consent | `consent=true` mandatory; recorded in sealed package |
| Jurisdiction tag | Required metadata (country / agency / legal basis) |
| Stronger provenance | Every audio chunk + detection event must be CID-addressable and braid-journaled |
| No automated decisions | System never recommends detention, charge, or clearance; only surfaces indicators |
| Retention policy | Configurable; default is long-term immutable archive |
| Dual control | Optional second-officer acknowledgement of high-priority cues |
| Export package | Court / oversight ready: transcript, signals, model versions, confidence, raw feature summaries, disclaimer |

## Main Flow

1. Operator starts session: `lie_start_session(mode="government", consent=true, jurisdiction="...", subject_id="...")`
2. Optional calm baseline captured with `lie_set_baseline`
3. Live audio (and later video) fed continuously
4. Earpiece receives only high-confidence, carefully worded cues
5. Operator may acknowledge cues; acknowledgements are logged
6. On seal, package is written with full government metadata and the permanent disclaimer that all signals are probabilistic observations only

## Prohibited Behaviours

- Presenting any score as definitive proof of deception or intent
- Automatic escalation or decision making
- Mixing simulated / hypothetical content into the sealed government package
- Operating without recorded consent in this mode

## Integration Points

- mem20liez live session (already supports `mode="government"`)
- Future: automatic `remember()` of the sealed package into grounded memory with `origin="grounded"` and government tags
- Future: braid event type `gov.interview.sealed`
- Future: export renderer for oversight packages

## Acceptance Criteria

- [x] Mode `government` accepted by `lie_start_session` and requires consent
- [x] Sealed package carries jurisdiction / subject / consent metadata
- [ ] Dual-control acknowledgement path
- [ ] Braid-journaled seal event
- [ ] Oversight export format
