# mem20contextcompressionforgez — Context Compression Forge

First-class mem20 subsystem for context compression (lossy/ratio compression, extractive summary, compression ratio, key terms, token-budget forging) with **6 context-compression peers**, SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app, and real MCP tools.

## Peers (6)
`mem20eventstreamsuperhighwayz`, `mem20loreragcontentgeneratorz`, `mem20mixedinitiativefocusenginez`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`, `mem20causalroutingbrainz`.

## Python API (runnable)
```python
from mem20contextcompressionforgez.domain import compress, extractive_summary, compression_ratio, key_terms, forge_context, compression_report, probe
print("..." in compress("a b c d e f g h", 0.5))  # True
print(len(extractive_summary("A. B. C. D.", 2)))   # 2
print(compression_ratio("hello","he"))               # 0.4
print(isinstance(key_terms("memory compression memory system"), list))  # True
r = compression_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])                                 # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20contextcompressionforgez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20contextcompressionforgez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20contextcompressionforgez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20contextcompressionforgez serve --port 8793
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/contextcompressionforgez/index.html` (no Vite edits). WAL `~/.mem20/mem20contextcompressionforgez/state.sqlite3`.

## MCP & registration
`ContextCompressionForgeToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20contextcompressionforgez/mem20contextcompressionforgez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20contextcompressionforgez
```
Target **7/7**.
