# mem20twinz — Twinz (Twin Runtime)

First-class mem20 crew runtime for digital twins with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core APIs preserved (`estate_context` superset, `MEMBERS`/`__version__`, legacy `--members/--version`).

## Peers (6)
`mem20executiondigitaltwinz`, `mem20realtimebusinesstwinz`, `mem20counterfactualmemorysimulatorz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20twinz --members
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20twinz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20twinz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20twinz serve --port 8840
```
