# mem20servicebundlingenginez — Service Bundling Engine

First-class mem20 subsystem for service bundling (create/add/discount/health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20autonomousdealdeskz`, `mem20simz`, `mem20capabilitymarketplacez`, `mem20eventstreamsuperhighwayz`, `mem20universalhealthnervoussystemz`, `mem20revenueleakhunterz`.

## Python API (runnable)
```python
from mem20servicebundlingenginez.domain import create_bundle, add_service, discount, bundle_report, probe
b=create_bundle([{"price":5},{"price":3}]); discount(b,0.1); print(b["price"])  # 7.2
r=bundle_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20servicebundlingenginez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20servicebundlingenginez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20servicebundlingenginez serve --port 8830
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/servicebundlingenginez/index.html`.

## MCP & registration
`ServiceBundlingEngineToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20servicebundlingenginez/mem20servicebundlingenginez/tests -q --noconftest -p no:cacheprovider
```
Target **7/7**.
