# mem20revenueleakhunterz — Revenue Leak Hunter

First-class mem20 subsystem for revenue leak hunting (detect leaks, anomaly scoring, recoverable amounts) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20businessmodelsimulatorz`, `mem20autonomousdealdeskz`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20causalroutingbrainz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20revenueleakhunterz.domain import detect_leaks, anomaly_score, recoverable, leak_report, probe
leaks=detect_leaks([{"id":"a","amount":5}], {"a":10}); print(leaks[0]["delta"])  # -5
print(recoverable(leaks))  # 5.0
r=leak_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20revenueleakhunterz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20revenueleakhunterz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20revenueleakhunterz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20revenueleakhunterz serve --port 8817
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/revenueleakhunterz/index.html` (no Vite edits).

## MCP & registration
`RevenueLeakHunterToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20revenueleakhunterz/mem20revenueleakhunterz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20revenueleakhunterz
```
Target **7/7**.
