# UC-MEM-AV-001 — Live Audio/Video Memory Inputs + Professional Assistance

**Status:** Active development  
**Subsystem:** mem20liez + future live AV pipeline  
**Related:** UC-MEM-AV-GOV-001 (government)

## Goal

Accept live and recorded audio/video as grounded memory inputs. Provide real-time probabilistic behavioural signals (voice stress, micro-expression, emotion, manipulation, deception indicators) and deliver cautious TTS earpiece cues to the professional. On session end, seal a complete, braid-provable package suitable for later audit or court use.

## Core Capabilities

- Live session management (`lie_start_session` … `lie_seal_session`)
- Real voice-stress detection (numpy acoustic features + optional personal baseline)
- Scaffold detectors for micro-expression, emotion, manipulation, deception fusion
- Earpiece cue generation (priority-ranked, confidence-gated)
- Immutable sealed package with mandatory disclaimer

## Scenarios Covered

1. **Interrogation assistance** — officer receives voice-stress and other indicators via earpiece; full transcript + signals sealed for court.
2. **Therapy support** — therapist receives optional low-intrusion cues; grounded session log with voice-change and topic links.
3. **Clinical encounter** — physician receives history-relevant cues and stress indicators; package sealed to medical record.

## Non-negotiable Rules

- All signals are probabilistic observations only.
- Never written as definitive “the subject is lying”.
- Grounded partition only; contamination firewall enforced.
- Consent required for interrogation / clinical / government modes.
- Full provenance and model version recorded.

## MCP Tools

See `mem20liez/mem20liez/mcp_tools.py`:

- `lie_start_session`
- `lie_set_baseline`
- `lie_feed_audio`
- `lie_feed_transcript`
- `lie_get_cues`
- `lie_acknowledge_cue`
- `lie_seal_session`
- `lie_list_sessions`

## Acceptance Criteria (current)

- [x] Voice-stress detector produces real features and baseline deviation scores
- [x] MCP tool surface defined and callable
- [x] Sealed package contains detections, cues, disclaimer
- [ ] Full video / micro-expression engine
- [ ] Automatic write of sealed package into main grounded store + braid
- [ ] End-to-end live microphone → earpiece path
