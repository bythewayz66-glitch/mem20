# mem20universalintegrationcompilerz — Universal Integration Compiler

First-class mem20 subsystem for universal integration compilation (compile_integration/validate_mapping/transform/integration_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20protocolautodiscoveryenginez`, `mem20runtimecompatibilityenginez`, `mem20agentoutputcompilerz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20faultcontainmentcellsz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20universalintegrationcompilerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20universalintegrationcompilerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20universalintegrationcompilerz serve --port 8843
```
