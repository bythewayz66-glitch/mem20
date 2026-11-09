# mem20realtimebusinesstwinz — Real-Time Business Twin

First-class mem20 subsystem for real-time business twins (live KPIs, threshold alerts, what-if scenarios, twin health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20simz`, `mem20demandforecastandcapacitybrainz`, `mem20eventstreamsuperhighwayz`, `mem20universalhealthnervoussystemz`, `mem20simz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20realtimebusinesstwinz.domain import create_twin, update_kpi, check_alerts, scenario, business_twin_report, probe
t=create_twin("acme"); update_kpi(t,"churn",0.2); print(check_alerts(t,{"churn":0.1})[0]["kpi"])  # churn
print(scenario(t,{"revenue":10})["delta"])
r=business_twin_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimebusinesstwinz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimebusinesstwinz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimebusinesstwinz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimebusinesstwinz serve --port 8811
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/realtimebusinesstwinz/index.html` (no Vite edits).

## MCP & registration
`RealTimeBusinessTwinToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20realtimebusinesstwinz/mem20realtimebusinesstwinz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20realtimebusinesstwinz
```
Target **7/7**.
