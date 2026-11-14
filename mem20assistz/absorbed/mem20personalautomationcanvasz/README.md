# mem20personalautomationcanvasz — Personal Automation Canvas

First-class mem20 subsystem for personal automation canvas (create_canvas/add_workflow/add_trigger/run_workflow/canvas_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20autonomousworkcellsz`, `mem20agentoutputcompilerz`, `mem20selfhealingplansz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20personalautomationcanvasz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20personalautomationcanvasz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20personalautomationcanvasz serve --port 8851
```
