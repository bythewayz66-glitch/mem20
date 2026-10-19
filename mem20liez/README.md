# mem20liez

**Real-time behavioural signal detection for mem20 live sessions.**

Provides probabilistic detectors for:

- **Voice stress** (real — numpy acoustic features + optional personal baseline)
- Micro-expressions (scaffold)
- Emotion (scaffold)
- Manipulation indicators (scaffold)
- Deception indicators (scaffold fusion)

These signals feed the live AV assistance pipeline (interrogation, clinical, therapy, government modes) and are written only as **observations with confidence** into grounded memory. They are never treated as definitive truth.

## Design Principles (non-negotiable)

1. **Probabilistic only** — every output carries a confidence score and model version.
2. **No silent claims** — the system never says “the subject is lying”. It says “voice-stress deviation 0.62 under model X”.
3. **Grounded partition only** — raw signals + derived scores are recorded with full provenance.
4. **Braid-journaled** (integration pending) — every detection event can be proven.
5. **Pluggable backends** — classical / statistical first; learned models are optional and versioned.
6. **High-stakes honesty** — suitable for court / medical / government audit only because the limitations are explicit.

## Current Status

| Detector              | Status                          |
|-----------------------|---------------------------------|
| Voice stress          | **Real** (numpy, baseline-aware)|
| Micro-expression      | Scaffold                        |
| Emotion               | Scaffold                        |
| Manipulation          | Scaffold                        |
| Deception fusion      | Scaffold                        |
| MCP tool surface      | **Present** (`mcp_tools.py`)    |
| Use-case docs         | `docs/use-cases/UC-MEM-AV-*.md` |

## Quick start

```python
from mem20liez import LieDetector, LiveLieSession

detector = LieDetector()
session = LiveLieSession(detector, mode="interrogation")

# optional: set a calm baseline first
# session.detector.set_baselines(voice=baseline_features)

session.feed_audio(pcm_bytes)
cues = session.get_earpiece_cues()
package = session.seal()
```

MCP tools: `lie_start_session`, `lie_set_baseline`, `lie_feed_audio`, `lie_get_cues`, `lie_seal_session`, …

## Government mode

```python
lie_start_session(mode="government", consent=True, jurisdiction="US-FED", subject_id="...")
```

Requires explicit consent. Sealed packages carry jurisdiction metadata and the permanent probabilistic disclaimer.

## Licence

Same as parent mem20 (MIT).
