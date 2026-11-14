# mem20sensorymemoryingestz — Sensory Memory Ingest

First-class mem20 subsystem for sensory memory ingest (ingest/filter_by_modality/recent/ingest_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20episodicmemorygraphz`, `mem20eventstreamsuperhighwayz`, `mem20rewardforgez`, `mem20capabilitymarketplacez`, `mem20universalhealthnervoussystemz`, `mem20faultcontainmentcellsz`.

## Python API (runnable)
```python
from mem20sensorymemoryingestz.domain import ingest, filter_by_modality, recent, ingest_health, ingest_report, probe
s={"entries":[]}; ingest(s,"hi","text"); print(ingest_health(s)["entries"])  # 1
r=ingest_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20sensorymemoryingestz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20sensorymemoryingestz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20sensorymemoryingestz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20sensorymemoryingestz serve --port 8829
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/sensorymemoryingestz/index.html` (no Vite edits).

## MCP & registration
`SensoryMemoryIngestToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20sensorymemoryingestz/mem20sensorymemoryingestz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20sensorymemoryingestz
```
Target **7/7**.
