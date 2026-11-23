# mem20styleguideagentz — Style Guide Agent

First-class mem20 subsystem for style guide checking (check/fix/style_score/style_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20agentoutputcompilerz`, `mem20autonomoussoftwarefoundryz`, `mem20rewardforgez`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20universalhealthnervoussystemz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20styleguideagentz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20styleguideagentz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20styleguideagentz serve --port 8838
```
