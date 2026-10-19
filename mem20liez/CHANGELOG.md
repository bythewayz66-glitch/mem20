# mem20liez changelog

## 0.2.0 — 2026-10-19

### Added
- **Real voice-stress detector** (`detectors/voice_stress.py`)
  - RMS, zero-crossing rate, autocorrelation pitch, energy variance, burst rate
  - Optional personal baseline → deviation score and interpretation
- **Real micro-expression detector** (`detectors/micro_expression.py`)
  - numpy/PIL frame differencing, regional intensity bands, baseline support
- **Live path** (`live.py`)
  - Mic capture via sounddevice or pyaudio; WAV offline replay always available
  - Earpiece TTS: pyttsx3 → espeak → macOS say → stdout
  - `run_live_session()` convenience API
- **CLI** `fs-lie` (`cli.py`): `status`, `live`
- **MCP surface** (`mcp/tools/lie_tools.py` + `mem20liez/mcp_tools.py`)
  - Full tool set including government dual-control
  - Seal writes to grounded memory (`remember`) and braid (`liez.session.sealed`)
- **Government mode** on `LiveLieSession` + `lie_dual_acknowledge`
- Use-case docs: `docs/use-cases/UC-MEM-AV-001.md`, `UC-MEM-AV-GOV-001.md`
- Tests: `test_voice_stress.py`, `test_micro_expression.py`, `test_basic.py`

### Changed
- Cue generator emits mode-aware text for real voice-stress and micro-expression scores
- Package version 0.2.0; optional extras `[live]`, `[audio]`, `[vision]`

### Notes
- Emotion / manipulation / deception fusion remain scaffolds (honest confidence 0.0)
- MCP server may need one-time `_server_impl.py` recovery — see INTEGRATION.md

## 0.1.0 — 2026-10-19

- Initial scaffold: types, pipeline, session, all detectors as placeholders
