# mem20liez

**Real-time behavioural signal detection for mem20 live sessions.**

| Detector | Status |
|----------|--------|
| **Voice stress** | Real — numpy acoustic features + baseline |
| **Micro-expression** | Real — numpy/PIL frame-diff + regional AU proxies |
| Emotion | Scaffold |
| Manipulation | Scaffold |
| Deception fusion | Scaffold |
| **Live mic → earpiece** | Real — sounddevice/pyaudio or WAV replay + TTS |
| MCP tools | `mcp/tools/lie_tools.py` |

## Live path

```bash
# status (backends)
fs-lie status

# offline WAV replay (always works)
fs-lie live --wav sample.wav --mode interrogation --out sealed.json

# live mic (needs: pip install sounddevice)
fs-lie live --duration 30 --mode government
```

Python:

```python
from mem20liez import LiveLieSession, LieDetector
from mem20liez.live import LiveCapture, EarpieceTTS, run_live_session

result = run_live_session(mode="interrogation", duration_s=20)
# or WAV:
result = run_live_session(mode="clinical", wav_path="session.wav")
```

## Design rules

- Probabilistic only — confidence + model version on every result
- Never claims “the subject is lying”
- Grounded partition on seal; optional braid journal via MCP `lie_seal_session`
- Government mode requires consent + supports dual-control ack

## Licence

MIT (same as mem20)
