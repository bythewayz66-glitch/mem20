# mem20visualagentblackboardz — Visual Agent Blackboard

First-class mem20 subsystem for visual agent blackboard (create_blackboard/post/read/clear/blackboard_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20autonomousworkcellsz`, `mem20agentoutputcompilerz`, `mem20realtimeteampresencez`, `mem20episodicmemorygraphz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20visualagentblackboardz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20visualagentblackboardz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20visualagentblackboardz serve --port 8844
```
