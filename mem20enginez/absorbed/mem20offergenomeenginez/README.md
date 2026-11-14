# mem20offergenomeenginez — Offer Genome Engine

First-class mem20 subsystem for offer genome evolution (create_genome/mutate/fitness/evolve) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20offerassemblyfabricz`, `mem20autonomousdealdeskz`, `mem20simz`, `mem20simz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20offergenomeenginez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20offergenomeenginez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20offergenomeenginez serve --port 8848
```
