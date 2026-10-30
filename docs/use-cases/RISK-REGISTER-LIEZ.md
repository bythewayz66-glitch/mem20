# Risk Register — mem20liez (Government & Clinical Modes)

**Version:** 2026-10-30  
**Owner:** mem20 maintainers  
**Scope:** `mode=government` and `mode=clinical` (and by extension interrogation)

| ID | Risk | Likelihood | Impact | Mitigation (in code / process) | Residual |
|----|------|------------|--------|--------------------------------|----------|
| R1 | Operator treats scores as definitive proof of deception | Med | Critical | Hard language ban; disclaimer on every seal; confidence + model id required; prohibited-use gate | Low |
| R2 | Government mode run without consent | Med | Critical | `consent=true` + `consent_attested_by` required at session start and seal | Low |
| R3 | Single-officer high-stakes decision | Med | High | Dual-control required for high-priority cues before seal (`lie_dual_acknowledge`) | Low |
| R4 | Use as polygraph substitute / medical device | Low | Critical | Explicit prohibited uses; seal contamination check rejects diagnosis keys | Low |
| R5 | Automated detention / charge / clearance | Low | Critical | Prohibited-use list checked at start and seal | Low |
| R6 | Untrained operator in high-stakes mode | Med | High | `lie_acknowledge_training` required; training version recorded on package | Med |
| R7 | Contamination of grounded memory with definitive claims | Med | High | `seal_contamination_check` forces `epistemic_status=observed_indicator`, strips banned annotation keys | Low |
| R8 | Regulatory gap (no formal legal/HIPAA review) | High | High | Legal-review request package published; do not deploy clinically until reviewed | High |
| R9 | Classical detectors over-interpreted | Med | Med | Confidence capped; scaffolds honest; docs state “indicators only” | Med |
| R10 | Covert use / employment screening without notice | Low | High | Listed in prohibited uses; consent gate | Med |
| R11 | Missing formal oversight export | Med | Med | Future work flagged in UC-MEM-AV-GOV-001; seal package is the interim audit artefact | Med |
| R12 | Subject data retention / rights not implemented | High | High | Out of band — retention policy must be defined by deploying organisation | High |

## Acceptance for residual “High” items

- **R8**: Do not enable clinical or government production use until external legal review is complete (see `LEGAL-REVIEW-REQUEST.md`).
- **R12**: Deploying organisation must supply retention, access, and deletion policy; mem20liez records the package but does not own the policy.

## Review cadence

Re-open this register on any of: new detector engine, new mode, change to consent/dual-control, or external legal opinion.
