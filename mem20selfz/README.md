# mem20selfz — Selfz

First-class mem20 subsystem/crew runtime for self-model integration with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core APIs preserved (`estate_context`, `MEMBERS`, `__version__`, legacy `--members/--version`).

## Peers (6)
`mem20episodicmemorygraphz`, `mem20rewardforgez`, `mem20causalroutingbrainz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20universalhealthnervoussystemz`.

## Python API (runnable)
```python
from mem20selfz.domain import self_report, probe, estate_context
r=self_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
print(estate_context()["peer_count"])  # 6
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfz --members
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfz serve --port 8828
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/selfz/index.html` (no Vite edits).

## MCP & registration
`SelfzToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20selfz/mem20selfz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20selfz
```
Target **7/7**.
