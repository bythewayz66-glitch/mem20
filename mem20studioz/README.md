# mem20studioz — Studioz (Studio Runtime)

First-class mem20 crew runtime for studio pipelines with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core APIs preserved (`estate_context` superset, `MEMBERS`/`__version__`, legacy `--members/--version`).

## Peers (6)
`mem20audiovoiceandmusicpipelinez`, `mem20rigginganimationandmotionpipelinez`, `mem20productionplanningandtaskorchestrationpipelinez`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20autonomousworkcellsz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20studioz --members
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20studioz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20studioz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20studioz serve --port 8837
```
