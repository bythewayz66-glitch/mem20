# mem20roamingworkloadschedulerz — Roaming Workload Scheduler

First-class mem20 subsystem for roaming workload scheduling (schedule, migrate, node load, health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20zerotouchnodeswarmz`, `mem20autonomousworkcellsz`, `mem20demandforecastandcapacitybrainz`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20roamingworkloadschedulerz.domain import schedule, migrate, scheduler_report, probe
nodes=[{"id":"a","load":0},{"id":"b","load":5}]; print(schedule([{"id":"w","cost":1}],nodes)[0]["node"])  # a
print(migrate("w","a","b")["to"])  # b
r=scheduler_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20roamingworkloadschedulerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20roamingworkloadschedulerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20roamingworkloadschedulerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20roamingworkloadschedulerz serve --port 8820
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/roamingworkloadschedulerz/index.html` (no Vite edits).

## MCP & registration
`RoamingWorkloadSchedulerToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20roamingworkloadschedulerz/mem20roamingworkloadschedulerz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20roamingworkloadschedulerz
```
Target **7/7**.
