# mem20productledgrowthsimulatorz — Product-Led Growth Simulator

First-class mem20 subsystem for product-led growth simulation (funnels, viral coefficient, retention curves, growth scoring) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20businessmodelsimulatorz`, `mem20customerlifecycleenginez`, `mem20autonomoussaleslaboratoryz`, `mem20crossproductloyaltygraphz`, `mem20demandforecastandcapacitybrainz`, `mem20eventstreamsuperhighwayz`.

## Python API (runnable)
```python
from mem20productledgrowthsimulatorz.domain import funnel, viral_coefficient, retention_curve, growth_score, simulate, plg_report, probe
print(funnel(100,[{"conversion":0.5}]))  # [100, 50]
print(viral_coefficient(2,0.1))  # 0.2
print(simulate({"starting_users":100,"invites":2,"invite_conv":0.1})["viral_k"])  # 0.2
r=plg_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20productledgrowthsimulatorz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20productledgrowthsimulatorz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20productledgrowthsimulatorz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20productledgrowthsimulatorz serve --port 8808
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/productledgrowthsimulatorz/index.html` (no Vite edits).

## MCP & registration
`ProductLedGrowthSimulatorToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20productledgrowthsimulatorz/mem20productledgrowthsimulatorz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20productledgrowthsimulatorz
```
Target **7/7**.
