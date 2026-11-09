# mem20remoteexperimentlabz — Remote Experiment Lab

First-class mem20 subsystem for remote experiment lab (create, run, compare, health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20autonomousworkcellsz`, `mem20zerotouchnodeswarmz`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20simz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20remoteexperimentlabz.domain import create_experiment, run, compare, experiment_report, probe
e=create_experiment("x",{"a":1}); run(e, lambda p: {"score":p["a"]}); print(e["results"]["score"])  # 1
r=experiment_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20remoteexperimentlabz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20remoteexperimentlabz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20remoteexperimentlabz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20remoteexperimentlabz serve --port 8815
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/remoteexperimentlabz/index.html` (no Vite edits).

## MCP & registration
`RemoteExperimentLabToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20remoteexperimentlabz/mem20remoteexperimentlabz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20remoteexperimentlabz
```
Target **7/7**.
