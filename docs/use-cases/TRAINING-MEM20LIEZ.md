# mem20liez Operator Training

**Training version:** `2026-10-30`  
**Required for:** `interrogation`, `clinical`, `government` modes  
**Acknowledgement tool:** `lie_acknowledge_training(operator_id, version="2026-10-30")`

## Learning objectives

After this training an operator can:

1. State that every signal is probabilistic and never definitive proof of deception or intent.
2. List the prohibited uses and refuse them.
3. Correctly start a consented session and seal it only when gates pass.
4. Perform dual-control acknowledgement in government mode.
5. Interpret earpiece cues as *hypotheses to investigate*, not findings.

## Module 1 — What mem20liez is (and is not)

- **Is:** real-time voice-stress and micro-motion indicators + rule-based linguistic cues; live earpiece; immutable sealed package with full provenance.
- **Is not:** a polygraph, a medical device, a lie detector, or a source of clinical diagnosis.
- Every detection carries `confidence.score`, `model_id`, and `model_version`.
- The sealed package always includes the standard disclaimer.

## Module 2 — Modes and consent

| Mode | Consent required | Dual-control | Typical use |
|------|------------------|--------------|-------------|
| generic | No | No | Demo / research |
| therapy | No* | No | Optional low-intrusion cues |
| clinical | **Yes** | No | Clinical interview support |
| interrogation | **Yes** | No | Investigative interview |
| government | **Yes** | **Yes** | High-stakes / oversight |

*Therapy mode does not currently hard-require consent in code; organisational policy may still require it.

Consent is recorded as `consent=true` + `consent_attested_by` and is re-checked at seal.

## Module 3 — Prohibited uses (memorise)

- automated_detention / automated_charge / automated_clearance
- definitive_deception_claim
- clinical_diagnosis / medical_device_claim
- polygraph_substitute
- covert_surveillance_without_warrant
- employment_screening_without_notice
- immigration_adjudication / child_custody_determination

Calling `lie_start_session` or `lie_seal_session` with any of these in `intended_uses` is refused.

## Module 4 — Dual control (government)

1. High-priority cues (priority ≥ 3) appear in `lie_get_cues` → `high_priority_ids`.
2. Two *distinct* officer IDs must call `lie_dual_acknowledge` for each such cue.
3. Seal is refused until every high-priority cue has dual acknowledgement.

## Module 5 — Contamination firewall

- Sealed packages are tagged `origin=grounded`, `epistemic_status=observed_indicator`, `is_definitive_finding=false`.
- Annotation keys such as `diagnosis`, `legal_finding`, `deception_confirmed`, `guilty`, `detain` are rejected at seal.
- This protects the main mem20 grounded store from being polluted by overclaims.

## Module 6 — Practical checklist

```
[ ] Operator has called lie_acknowledge_training
[ ] Subject consent recorded (high-stakes modes)
[ ] Jurisdiction / subject_id set when required
[ ] No prohibited intended_uses
[ ] Baseline captured when practical
[ ] Cues treated as investigation prompts only
[ ] Government: dual-ack all high-priority cues
[ ] Seal and archive package; never edit detections post-seal
```

## Acknowledgement

```text
lie_acknowledge_training(operator_id="<your-id>", version="2026-10-30")
```

Without this, high-stakes session start is refused.
