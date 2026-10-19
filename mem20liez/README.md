# mem20liez

**Real-time behavioural signal detection for mem20 live sessions.**

Provides probabilistic detectors for:

- Micro-expressions
- Voice stress
- Emotion
- Manipulation indicators
- Deception indicators

These signals feed the live AV assistance pipeline (interrogation, clinical, therapy modes) and are written only as **observations with confidence** into grounded memory. They are never treated as definitive truth.

## Design Principles (non-negotiable)

1. **Probabilistic only** — every output carries a confidence score and model version.
2. **No silent claims** — the system never says “the subject is lying”. It says “deception indicator fired at 0.73 confidence under model X”.
3. **Grounded partition only** — raw signals + derived scores are recorded with full provenance.
4. **Braid-journaled** — every detection event can be proven.
5. **Pluggable backends** — classical / statistical first; learned models are optional and versioned.
6. **High-stakes honesty** — suitable for court / medical / therapeutic audit only because the limitations are explicit.

## Quick status

| Detector              | Status          | Notes                                      |
|-----------------------|-----------------|--------------------------------------------|
| Micro-expression      | Scaffold        | Frame-level facial action units            |
| Voice stress          | Scaffold        | Pitch, jitter, shimmer, pause analysis     |
| Emotion               | Scaffold        | Valence / arousal + categorical            |
| Manipulation          | Scaffold        | Linguistic + behavioural patterns          |
| Deception             | Scaffold        | Fusion of the above + baseline deviation   |

## Integration

```python
from mem20liez import LieDetector, LiveLieSession

detector = LieDetector()
session = LiveLieSession(detector, mode="interrogation")

# feed audio / video chunks from the live AV pipeline
session.feed_audio(chunk)
session.feed_video(frame)

cues = session.get_earpiece_cues()   # TTS-ready strings
# ... later
result = session.seal()             # writes grounded package
```

## Package layout

```
mem20liez/
├── README.md
├── pyproject.toml
├── mem20liez/
│   ├── __init__.py
│   ├── types.py
│   ├── detectors/
│   │   ├── __init__.py
│   │   ├── micro_expression.py
│   │   ├── voice_stress.py
│   │   ├── emotion.py
│   │   ├── manipulation.py
│   │   └── deception.py
│   ├── pipeline.py
│   ├── session.py
│   └── cues.py
└── tests/
    └── test_basic.py
```

## Licence

Same as parent mem20 (MIT).
