# mem20planetarybatchfabricz — Planetary Batch Fabric

First-class mem20 subsystem for planetary batch fabric (submit_job/schedule/job_status/fabric_health/retry) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20roamingworkloadschedulerz`, `mem20autonomousworkcellsz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20autonomousrecoverydirectorz`, `mem20agentoutputcompilerz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20planetarybatchfabricz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20planetarybatchfabricz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20planetarybatchfabricz serve --port 8856
```
