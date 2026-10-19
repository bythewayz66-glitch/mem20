# UC-MEM-AV-001 — Live Audio/Video Memory + Professional Assistance

**Status:** Implemented (voice stress + micro-expression + live path + MCP)  
**Subsystem:** mem20liez  
**Related:** [UC-MEM-AV-GOV-001](./UC-MEM-AV-GOV-001.md)

## Goal

Accept live and recorded audio/video as grounded memory inputs. Provide real-time probabilistic behavioural signals and TTS earpiece cues. On session end, seal an immutable package for audit or court use.

## Implemented capabilities

| Capability | Implementation |
|------------|----------------|
| Voice stress | `detectors/voice_stress.py` — real numpy features + baseline |
| Micro-expression | `detectors/micro_expression.py` — real numpy/PIL motion + regions |
| Live capture | `live.py` — mic (sounddevice/pyaudio) or WAV |
| Earpiece cues | `cues.py` + `EarpieceTTS` |
| Session lifecycle | `LiveLieSession` + MCP `lie_*` tools |
| Grounded seal | `lie_seal_session` → `remember()` + braid |

## Scenarios

1. **Interrogation** — officer receives stress / micro-motion cues; sealed package for record.
2. **Therapy** — optional low-intrusion cues; grounded session log.
3. **Clinical** — stress indicators + history context (history recall is separate memory tools).

## How to run

```bash
pip install -e mem20liez[live]
fs-lie live --wav interview.wav --mode interrogation --out sealed.json
```

```python
from mem20liez.live import run_live_session
run_live_session(mode="interrogation", wav_path="interview.wav")
```

MCP: `lie_start_session` → `lie_feed_audio` / `lie_set_baseline` → `lie_get_cues` → `lie_seal_session`.

## Rules

- Signals are observations with confidence only.
- Consent required for interrogation / clinical / government.
- Sealed package always includes the probabilistic disclaimer.

## Acceptance (current)

- [x] Real voice-stress features and baseline deviation
- [x] Real micro-expression motion/region scoring
- [x] Live/WAV path + TTS fallback
- [x] MCP tools + grounded/braid seal
- [ ] Full face-detector / learned AU model (optional upgrade)
- [ ] Always-on production mic service unit
