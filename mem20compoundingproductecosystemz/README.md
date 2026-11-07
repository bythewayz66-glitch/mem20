# mem20compoundingproductecosystemz — Compounding Product Ecosystem

First-class mem20 subsystem for compounding product ecosystems (synergies, network value, compound growth, ecosystem health, cross-sell matrix) with **6 product-ecosystem peers**, SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app, and real MCP tools.

## Peers (6)
`mem20crossproductloyaltygraphz`, `mem20customerlifecycleenginez`, `mem20businessmodelsimulatorz`, `mem20autonomoussaleslaboratoryz`, `mem20demandforecastandcapacitybrainz`, `mem20acquisitionandpartnershipscoutz`.

## Python API (runnable)
```python
from mem20compoundingproductecosystemz.domain import synergy, network_value, compound_growth, ecosystem_health, cross_sell_matrix, ecosystem_report, probe, estate_context
print(synergy({"users":["a"],"value":1},{"users":["a"],"value":2}) >= 0.1)  # True
print(network_value(10) > 0)  # True
g = compound_growth(100, 0.1, 3); print(len(g), g[-1] > 100)  # 3 True
r = ecosystem_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"], estate_context()["peer_count"])  # True 6
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20compoundingproductecosystemz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20compoundingproductecosystemz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20compoundingproductecosystemz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20compoundingproductecosystemz serve --port 8792
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/compoundingproductecosystemz/index.html` (no Vite edits). State `/root/.mem20/mem20compoundingproductecosystemz/state.sqlite3` (WAL).

## MCP & registration
`CompoundingProductEcosystemToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20compoundingproductecosystemz/mem20compoundingproductecosystemz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20compoundingproductecosystemz
```
Target **7/7**.
