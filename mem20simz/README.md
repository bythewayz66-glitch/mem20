# mem20simz — Simz (Simulator Runtime)

First-class mem20 crew runtime for simulators with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core APIs preserved (`estate_context` superset, `MEMBERS`/`__version__`, legacy `--members/--version`).

## Peers (6)
`mem20simz`, `mem20twinz`, `mem20causalroutingbrainz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20faultcontainmentcellsz`.

## Python API (runnable)
```python
from mem20simz.domain import sim_report, probe, estate_context
r=sim_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20simz --members
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20simz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20simz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20simz serve --port 8831
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/simz/index.html`.

## MCP & registration
`SimzToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20simz -q --noconftest -p no:cacheprovider
```
Target **7/7**.
