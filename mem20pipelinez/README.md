# mem20pipelinez — crew pipeline runtime

Crew runtime for game-maker and software pipelines (12 members). Preserves core `MEMBERS`, `__version__`, and legacy CLI (`--version`, `--members`) while adding full depth spec: **6 peers**, SQLite WAL runtime, CLI subcommands, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. `estate_context` is a superset.

## Peers (6)
`mem20personalautomationcanvasz`, `mem20autonomousworkcellsz`, `mem20agentoutputcompilerz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20pipelinez --version
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20pipelinez --members
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20pipelinez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20pipelinez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20pipelinez serve --port 8855
```
