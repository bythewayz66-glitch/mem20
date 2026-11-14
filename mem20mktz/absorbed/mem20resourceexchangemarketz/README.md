# mem20resourceexchangemarketz — Resource Exchange Market

First-class mem20 subsystem for resource exchange markets (list/buy/price history/market health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20capabilitymarketplacez`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20causalroutingbrainz`, `mem20simz`, `mem20crossproductloyaltygraphz`.

## Python API (runnable)
```python
from mem20resourceexchangemarketz.domain import list_resource, buy, market_report, probe
l=list_resource("alice","cpu",10,2.0); print(buy(l,"bob",3)["cost"])  # 6.0
r=market_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20resourceexchangemarketz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20resourceexchangemarketz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20resourceexchangemarketz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20resourceexchangemarketz serve --port 8816
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/resourceexchangemarketz/index.html` (no Vite edits).

## MCP & registration
`ResourceExchangeMarketToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20resourceexchangemarketz/mem20resourceexchangemarketz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20resourceexchangemarketz
```
Target **7/7**.
