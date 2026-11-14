# mem20visualdataflowcomposerz — Visual Dataflow Composer

First-class mem20 subsystem for visual dataflow composition (create_pipeline/add_node/connect/execute/pipeline_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20visualagentblackboardz`, `mem20autonomousworkcellsz`, `mem20agentoutputcompilerz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20visualdataflowcomposerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20visualdataflowcomposerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20visualdataflowcomposerz serve --port 8845
```
