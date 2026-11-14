# mem20opportunityradarz — Opportunity Radar

First-class mem20 subsystem for opportunity radar (scan/score_opportunity/rank/alert/radar_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20autonomoussaleslaboratoryz`, `mem20simz`, `mem20causalroutingbrainz`, `mem20revenueleakhunterz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20opportunityradarz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20opportunityradarz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20opportunityradarz serve --port 8849
```
