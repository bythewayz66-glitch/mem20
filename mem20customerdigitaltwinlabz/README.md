# mem20customerdigitaltwinlabz — Customer Digital Twin Lab

First-class mem20 subsystem for customer digital twins (build twin, simulate behavior, predict churn, recommend action, twin accuracy) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app, and real MCP tools. Core API preserved.

## Peers (6)
`mem20customerlifecycleenginez`, `mem20simz`, `mem20demandforecastandcapacitybrainz`, `mem20crossproductloyaltygraphz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20customerdigitaltwinlabz.domain import build_twin, simulate_behavior, predict_churn, recommend_action, twin_report, probe
t=build_twin({"id":"c1","ltv":1200,"behavior":{"engagement":0.9,"recency_days":1}})
print(len(simulate_behavior(t,{"steps":3,"seed":0})))  # 3
print(recommend_action(t))  # upsell
r=twin_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20customerdigitaltwinlabz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20customerdigitaltwinlabz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20customerdigitaltwinlabz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20customerdigitaltwinlabz serve --port 8797
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. docs/app `docs/app/customerdigitaltwinlabz/index.html` (no Vite edits).

## MCP & registration
`CustomerDigitalTwinLabToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20customerdigitaltwinlabz/mem20customerdigitaltwinlabz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20customerdigitaltwinlabz
```
Target **7/7**.
