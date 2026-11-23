# RM-037 — Multimodal Task Capture (#338)

**Outcome:** Turn speech, sketches, screenshots, gestures, and rough notes into structured executable work.  
**Operation kind:** `ingest`.

## 1st-class implementation
- **Domain:** `capture/merge_captures/extract_action_items/capture_health` (legacy) plus `ingest_capture` producing structured executable task + action items across modalities.
- **Runtime:** `ingest` wired to domain + 6 peer signals.
- **Ecosystem (6 peers, unique set):** `mem20modalitybridgez`, `mem20sensorymemoryingestz`, `mem20intentcompilerz`, `mem20twinz`, `mem20agentoutputcompilerz`, `mem20episodicmemorygraphz`.

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20multimodaltaskcapturez execute '{"text":"build api. test api","source":"chat"}'
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20multimodaltaskcapturez/mem20multimodaltaskcapturez/tests/test_domain.py -q
```
Gateway `SUBSYSTEMS["mem20multimodaltaskcapturez"]`; docs `docs/app/multimodaltaskcapturez/index.html`; target 7/7.
