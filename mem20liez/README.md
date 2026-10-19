# mem20liez

**Real-time behavioural signal detection for mem20 live sessions.**

Probabilistic detectors for voice stress, micro-expressions, emotion, manipulation, and deception indicators. Feeds live AV assistance (interrogation, clinical, therapy, government) and seals sessions into grounded memory with full provenance.

> **Never claims certainty.** Every result carries confidence, model id/version, and an explicit disclaimer.

---

## Status matrix

| Component | Status | Engine |
|-----------|--------|--------|
| Voice stress | **Real** | numpy — RMS, ZCR, pitch, energy variance, burst rate + baseline |
| Micro-expression | **Real** | numpy/PIL — frame-diff + regional intensity |
| Emotion / manipulation / deception | Scaffold | honest placeholders |
| Live mic → earpiece | **Real** | sounddevice / pyaudio / WAV + TTS |
| MCP tools | **Real** | auto-wired into `mcp/server.py` on import |
| Grounded seal + braid | **Real** | on `lie_seal_session` |
| Government dual-control | **Real** | `lie_dual_acknowledge` |

---

## Install

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20/mem20liez
pip install -e ".[live]"
```

MCP server starts as usual (`python mcp/mcp_server.py` or systemd). Lie tools appear automatically — **no recovery step**.

---

## Quick start

### CLI

```bash
fs-lie status
fs-lie live --wav session.wav --mode interrogation --out sealed.json
fs-lie live --duration 30 --mode government
```

### Python

```python
from mem20liez.live import run_live_session

run_live_session(mode="interrogation", wav_path="session.wav")
# live mic:
run_live_session(mode="clinical", duration_s=60)
```

```python
from mem20liez import LieDetector, LiveLieSession

d = LieDetector()
r = d.process_audio(pcm_bytes)
print(r.value["interpretation"], r.confidence.score)

session = LiveLieSession(d, mode="interrogation")
session.feed_audio(pcm_bytes)
package = session.seal()
```

### MCP tools

`lie_status` · `lie_start_session` · `lie_set_baseline` · `lie_feed_audio` · `lie_feed_transcript` · `lie_get_cues` · `lie_acknowledge_cue` · `lie_dual_acknowledge` · `lie_seal_session` · `lie_list_sessions`

Government mode requires `consent=true`.

---

## Design rules

1. Probabilistic only — confidence + model version always present  
2. Never “the subject is lying” — indicator language only  
3. Grounded partition on seal; contamination firewall respected  
4. Consent required for interrogation / clinical / government  
5. Honest degradation when numpy / mic / TTS are missing  

---

## Docs

- [INTEGRATION.md](./INTEGRATION.md) — MCP auto-wiring  
- [CHANGELOG.md](./CHANGELOG.md)  
- [UC-MEM-AV-001](../docs/use-cases/UC-MEM-AV-001.md) · [UC-MEM-AV-GOV-001](../docs/use-cases/UC-MEM-AV-GOV-001.md)  

## Licence

MIT (same as mem20).
