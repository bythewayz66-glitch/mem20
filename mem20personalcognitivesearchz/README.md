# mem20personalcognitivesearchz — Personal Cognitive Search

First-class mem20 subsystem for personal cognitive search (index/query/rank/recall/search_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20episodicmemorygraphz`, `mem20contextcompressionforgez`, `mem20predictiverecallenginez`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20agentoutputcompilerz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20personalcognitivesearchz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20personalcognitivesearchz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20personalcognitivesearchz serve --port 8852
```
