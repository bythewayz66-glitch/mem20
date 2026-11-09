# mem20offerassemblyfabricz — Offer Assembly Fabric

First-class mem20 subsystem for offer assembly (create_offer/add_component/price_offer/publish/offer_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20autonomousdealdeskz`, `mem20servicebundlingenginez`, `mem20simz`, `mem20revenueleakhunterz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20offerassemblyfabricz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20offerassemblyfabricz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20offerassemblyfabricz serve --port 8847
```
