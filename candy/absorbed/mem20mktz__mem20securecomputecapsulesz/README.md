# mem20securecomputecapsulesz — Secure Compute Capsules

First-class mem20 subsystem for secure compute capsules (create, run, isolate, health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20faultcontainmentcellsz`, `mem20selfhealingplansz`, `mem20secretslessworkloadidentityz`, `mem20capabilitymarketplacez`, `mem20eventstreamsuperhighwayz`, `mem20deterministicconfigurationgraphz`.

## Python API (runnable)
```python
from mem20securecomputecapsulesz.domain import create_capsule, run_capsule, isolate, capsule_report, probe
c=create_capsule("1+1"); run_capsule(c, lambda code,lim: eval(code)); print(c["result"])  # 2
isolate(c); print(c["isolated"])  # True
r=capsule_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20securecomputecapsulesz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20securecomputecapsulesz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20securecomputecapsulesz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20securecomputecapsulesz serve --port 8824
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/securecomputecapsulesz/index.html` (no Vite edits).

## MCP & registration
`SecureComputeCapsulesToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20securecomputecapsulesz/mem20securecomputecapsulesz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20securecomputecapsulesz
```
Target **7/7**.
