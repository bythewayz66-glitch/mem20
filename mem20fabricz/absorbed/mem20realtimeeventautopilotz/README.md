# mem20realtimeeventautopilotz — Real-Time Event Autopilot

First-class mem20 subsystem for real-time event autopilot (event ingestion, rule evaluation, automated actions, throttling) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20selfhealingplansz`, `mem20causalroutingbrainz`, `mem20universalhealthnervoussystemz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20realtimeeventautopilotz.domain import ingest_event, evaluate_rules, autopilot, throttle, autopilot_report, probe
s={}; ingest_event(s,{"severity":9})
acts=evaluate_rules({"severity":9}, [{"condition":lambda e:e["severity"]>5,"action":"notify"}])
print(acts)  # ['notify']
r=autopilot_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeeventautopilotz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeeventautopilotz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeeventautopilotz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeeventautopilotz serve --port 8812
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/realtimeeventautopilotz/index.html` (no Vite edits).

## MCP & registration
`RealTimeEventAutopilotToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20realtimeeventautopilotz/mem20realtimeeventautopilotz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20realtimeeventautopilotz
```
Target **7/7**.
