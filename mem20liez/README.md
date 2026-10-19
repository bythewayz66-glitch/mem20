# mem20liez

**Real-time behavioural signal detection for mem20 live sessions.**

Probabilistic detectors for voice stress, micro-expressions, emotion, manipulation, and deception indicators. Feeds live AV assistance (interrogation, clinical, therapy, government) and seals sessions into grounded memory with full provenance.

> **Never claims certainty.** Every result carries confidence, model id/version, and an explicit disclaimer. The system reports *indicators*, not verdicts.

---

## Status matrix

| Component | Status | Engine |
|-----------|--------|--------|
| Voice stress | **Real** | numpy — RMS, ZCR, pitch (autocorr), energy variance, burst rate + baseline deviation |
| Micro-expression | **Real** | numpy/PIL — frame-diff motion energy, regional intensity (brows/eyes/nose/mouth) |
| Emotion | Scaffold | placeholder |
| Manipulation | Scaffold | placeholder |
| Deception fusion | Scaffold | placeholder |
| Live mic → earpiece | **Real** | sounddevice / pyaudio / WAV + TTS (pyttsx3 / espeak / say / stdout) |
| MCP tools | **Real** | `mcp/tools/lie_tools.py` |
| Grounded seal + braid | **Real** | `remember()` + `braid_commit` on seal |
| Government dual-control | **Real** | `lie_dual_acknowledge` |

---

## Install

```bash
cd mem20liez
pip install -e .
# optional live extras
pip install -e ".[live]"   # sounddevice, pyttsx3, Pillow
```

Requires Python ≥ 3.11, `numpy`, `pydantic≥2`.

---

## Quick start (Python)

### Voice stress on a PCM chunk

```python
from mem20liez import LieDetector

d = LieDetector()
# optional: set a calm baseline first
# base = d.voice.process_audio(calm_pcm)
# d.set_baselines(voice=base.raw_features)

r = d.process_audio(pcm_bytes)  # 16-bit mono PCM @ 16 kHz recommended
print(r.value["interpretation"], r.confidence.score)
# e.g. elevated_stress_indicator  0.72
```

### Micro-expression on a frame

```python
import numpy as np
from mem20liez import LieDetector

d = LieDetector()
frame = np.array(...)  # HxW gray or HxWx3, float 0–1 or uint8
r = d.process_video(frame)
print(r.value["interpretation"], r.value.get("micro_score"))
```

### Full live session → seal

```python
from mem20liez import LiveLieSession, LieDetector
from mem20liez.live import LiveCapture, EarpieceTTS, run_live_session

# One-shot convenience
result = run_live_session(mode="interrogation", duration_s=30)
# or offline:
result = run_live_session(mode="clinical", wav_path="session.wav")

print(result["package_summary"])
```

### Manual session control

```python
session = LiveLieSession(LieDetector(), mode="government")
session._meta = {"consent": True, "jurisdiction": "US-FED", "subject_id": "X"}

capture = LiveCapture(session, earpiece=EarpieceTTS())
capture.run_mic(duration_s=60)   # or capture.run_wav("file.wav")

package = session.seal(annotations={"officer_notes": "..."})
# package is ready for grounded memory / court audit
```

---

## CLI (`fs-lie`)

```bash
fs-lie status
# → numpy, PIL, mic backends, TTS backend

fs-lie live --wav sample.wav --mode interrogation --out sealed.json
fs-lie live --duration 45 --mode government
fs-lie live --wav call.wav --mode therapy --no-earpiece
```

| Flag | Meaning |
|------|---------|
| `--mode` | `interrogation` \| `therapy` \| `clinical` \| `government` \| `generic` |
| `--duration` | Seconds (mic mode) |
| `--wav` | WAV path (skips mic) |
| `--no-earpiece` | Do not speak cues |
| `--out` | Write full sealed package JSON |

---

## MCP tools

Registered via `mcp/tools/lie_tools.py` (LieToolsMixin).

| Tool | Purpose |
|------|---------|
| `lie_status` | Availability, active sessions, memory/braid status |
| `lie_start_session` | Start session (`mode`, `consent`, `jurisdiction`, …) |
| `lie_set_baseline` | Neutral voice baseline (base64 PCM) |
| `lie_feed_audio` | Push audio chunk (base64 PCM) |
| `lie_feed_transcript` | Linguistic / manipulation path |
| `lie_get_cues` | Pending TTS-ready earpiece cues |
| `lie_acknowledge_cue` | Primary operator ack |
| `lie_dual_acknowledge` | Second-officer ack (**government only**) |
| `lie_seal_session` | Seal → grounded `remember()` + optional braid |
| `lie_list_sessions` | Active sessions |

**Government mode** requires `consent=true`. Dual-control is only valid when `mode=government`.

On seal, the package is written to grounded memory (tags: `mem20liez`, `mode:…`, `sealed`) and a braid event `liez.session.sealed` is journaled when braid is available.

---

## Modes and cues

| Mode | Typical cue style |
|------|-------------------|
| interrogation | Operational, e.g. “Voice stress elevated… Consider slowing pace.” |
| government | Same, plus dual-control path |
| clinical | “Patient voice stress elevated…” |
| therapy | Low-intrusion wording |
| generic | Neutral indicator text |

Cues are confidence-gated and priority-ranked (1=info, 2=notable, 3=urgent).

---

## Design rules (non-negotiable)

1. **Probabilistic only** — confidence + model version on every result.
2. **No silent claims** — never “the subject is lying”; only indicator language.
3. **Grounded partition** on seal; contamination firewall respected.
4. **Consent** required for interrogation / clinical / government.
5. **Honest degradation** — missing numpy/mic/TTS fails with clear status, never invents signal.

---

## Package layout

```
mem20liez/
├── README.md                 # this file
├── INTEGRATION.md            # MCP server wiring + recovery
├── CHANGELOG.md
├── pyproject.toml
├── mem20liez/
│   ├── types.py
│   ├── pipeline.py           # LieDetector orchestrator
│   ├── session.py            # LiveLieSession
│   ├── cues.py               # earpiece cue text
│   ├── live.py               # mic / WAV / TTS path
│   ├── cli.py                # fs-lie
│   ├── mcp_tools.py          # standalone handlers + schemas
│   └── detectors/
│       ├── voice_stress.py   # REAL
│       ├── micro_expression.py  # REAL
│       ├── emotion.py
│       ├── manipulation.py
│       └── deception.py
└── tests/
```

MCP mixin: `mcp/tools/lie_tools.py`  
Use cases: `docs/use-cases/UC-MEM-AV-001.md`, `UC-MEM-AV-GOV-001.md`

---

## MCP server recovery

If `mcp/server.py` is a thin loader, restore the full implementation once:

```bash
git show 6a2bdaab2434611a2edee5d26b93bcc500edb87b:mcp/server.py > mem20liez/_server_impl.py
```

The loader subclasses `Mem20MCPServer` and registers all `lie_*` tools. Details: [INTEGRATION.md](./INTEGRATION.md).

---

## Licence

MIT (same as parent mem20).
