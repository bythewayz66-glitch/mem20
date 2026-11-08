# mem20personalworkflowtwinz — Personal Workflow Twin

First-class mem20 subsystem for personal workflow twin (create_twin/observe/suggest_improvements/efficiency_score/twin_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20personalautomationcanvasz`, `mem20autonomousworkcellsz`, `mem20agentoutputcompilerz`, `mem20episodicmemorygraphz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20personalworkflowtwinz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20personalworkflowtwinz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20personalworkflowtwinz serve --port 8854
```
