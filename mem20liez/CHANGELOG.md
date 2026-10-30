# mem20liez changelog

## 0.3.0 — 2026-10-30

### Added
- **Hard gates** (`gates.py`)
  - Consent required for interrogation / clinical / government
  - Dual-control records and enforcement for government high-priority cues
  - Formal prohibited-uses list (checked at start and seal)
  - Operator training acknowledgement gate
  - Contamination firewall on seal (`epistemic_status=observed_indicator`, banned annotation keys)
- **MCP tools**
  - `lie_acknowledge_training`
  - `lie_dual_acknowledge` (two distinct officer IDs)
  - `lie_prohibited_uses`
  - Structured `error_code` refusals from all gates
- **Manipulation detector** upgraded from scaffold to real rule-based linguistic indicators (confidence capped at 0.65)
- **Docs**
  - `docs/use-cases/RISK-REGISTER-LIEZ.md`
  - `docs/use-cases/TRAINING-MEM20LIEZ.md`
  - `docs/use-cases/LEGAL-REVIEW-REQUEST.md`

### Changed
- `LiveLieSession` construction and seal enforce consent, training, dual-control, and prohibited uses
- Seal package always carries the extended disclaimer and firewall block
- README status matrix and design rules updated

### Notes
- Emotion and deception-fusion remain scaffolds (honest confidence 0.0)
- Legal / regulatory review is **not** complete — see LEGAL-REVIEW-REQUEST.md; production clinical/government use is not authorised by this repo alone

## 0.2.0 — 2026-10-19

### Added
- **Real voice-stress detector** (`detectors/voice_stress.py`)
- **Real micro-expression detector** (`detectors/micro_expression.py`)
- **Live path** (`live.py`)
- **CLI** `fs-lie`
- **MCP surface** including government dual-control scaffold
- Use-case docs UC-MEM-AV-001 / UC-MEM-AV-GOV-001
- Tests for voice stress and micro-expression

### Notes
- Emotion / manipulation / deception fusion were scaffolds

## 0.1.0 — 2026-10-19

- Initial scaffold: types, pipeline, session, all detectors as placeholders
