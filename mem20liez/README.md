# mem20liez

**Real-time behavioural signal detection for mem20 live sessions.**

Probabilistic detectors for voice stress, micro-expressions, linguistic manipulation indicators, emotion, and deception fusion. Feeds live AV assistance (interrogation, clinical, therapy, government) and seals sessions into grounded memory with full provenance.

> **Never claims certainty.** Every result carries confidence, model id/version, and an explicit disclaimer.

---

## Status matrix

| Component | Status | Engine |
|-----------|--------|--------|
| Voice stress | **Real** | numpy — RMS, ZCR, pitch, energy variance, burst rate + baseline |
| Micro-expression | **Real** | numpy/PIL — frame-diff + regional intensity |
| Manipulation (linguistic) | **Real** | rule-based patterns; confidence capped at 0.65 |
| Emotion / deception fusion | Scaffold | honest placeholders (confidence 0.0) |
| Live mic → earpiece | **Real** | sounddevice / pyaudio / WAV + TTS |
| MCP tools | **Real** | consent, dual-control, training, prohibited-use gates |
| Grounded seal + braid | **Real** | contamination firewall on seal |
| Government dual-control | **Real** | `lie_dual_acknowledge` — two distinct officers |
| Operator training gate | **Real** | `lie_acknowledge_training` required for high-stakes modes |

---

## Hard gates (non-negotiable)

1. **Consent** — required for interrogation / clinical / government (`consent=true` + attested_by).
2. **Training** — operator must call `lie_acknowledge_training` before high-stakes sessions.
3. **Dual-control** — government mode: every high-priority cue needs two distinct officer IDs before seal.
4. **Prohibited uses** — automated detention/charge/clearance, definitive deception claims, clinical diagnosis, polygraph substitute, covert use without authority, etc. Refused at start and seal.
5. **Contamination firewall** — seal forces `epistemic_status=observed_indicator`, rejects diagnosis/legal-finding annotation keys, always attaches disclaimer.

See `mem20liez/gates.py` and `docs/use-cases/RISK-REGISTER-LIEZ.md`.

---

## Install

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20/mem20liez
pip install -e ".[live]"
```

---

## Quick start

### Training (required for high-stakes)

```text
lie_acknowledge_training(operator_id="officer-42", version="2026-10-30")
```

### CLI

```bash
fs-lie status
fs-lie live --wav session.wav --mode interrogation --out sealed.json
fs-lie live --duration 30 --mode government
```

### MCP tools

`lie_acknowledge_training` · `lie_start_session` · `lie_set_baseline` · `lie_feed_audio` · `lie_feed_transcript` · `lie_get_cues` · `lie_acknowledge_cue` · `lie_dual_acknowledge` · `lie_seal_session` · `lie_list_sessions` · `lie_prohibited_uses`

Government mode requires `consent=true`. High-priority cues require dual acknowledgement before seal.

---

## Design rules

1. Probabilistic only — confidence + model version always present  
2. Never “the subject is lying” — indicator language only  
3. Grounded partition on seal; contamination firewall respected  
4. Consent + training required for interrogation / clinical / government  
5. Honest degradation when numpy / mic / TTS are missing  

---

## Docs

- [INTEGRATION.md](./INTEGRATION.md)  
- [CHANGELOG.md](./CHANGELOG.md)  
- [UC-MEM-AV-001](../docs/use-cases/UC-MEM-AV-001.md) · [UC-MEM-AV-GOV-001](../docs/use-cases/UC-MEM-AV-GOV-001.md)  
- [RISK-REGISTER-LIEZ](../docs/use-cases/RISK-REGISTER-LIEZ.md)  
- [TRAINING-MEM20LIEZ](../docs/use-cases/TRAINING-MEM20LIEZ.md)  
- [LEGAL-REVIEW-REQUEST](../docs/use-cases/LEGAL-REVIEW-REQUEST.md)  

## Licence

MIT (same as mem20).
