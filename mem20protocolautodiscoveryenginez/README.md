# mem20protocolautodiscoveryenginez — Protocol Auto-Discovery Engine

First-class mem20 subsystem for protocol auto-discovery (detect protocol, parse headers, register/list handlers, protocol health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20faultcontainmentcellsz`, `mem20universalhealthnervoussystemz`, `mem20zerotouchnodeswarmz`, `mem20selfhealingplansz`.

## Python API (runnable)
```python
from mem20protocolautodiscoveryenginez.domain import detect_protocol, parse_headers, register_protocol, list_protocols, discovery_report, probe
print(detect_protocol("GET / HTTP/1.1"))  # http
print(parse_headers("A: b")["A"])  # b
r={}; register_protocol(r,"x","h"); print("x" in list_protocols(r))  # True
rep=discovery_report(); print(rep["ok"], len(rep["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20protocolautodiscoveryenginez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20protocolautodiscoveryenginez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20protocolautodiscoveryenginez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20protocolautodiscoveryenginez serve --port 8809
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/protocolautodiscoveryenginez/index.html` (no Vite edits).

## MCP & registration
`ProtocolAutoDiscoveryEngineToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20protocolautodiscoveryenginez/mem20protocolautodiscoveryenginez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20protocolautodiscoveryenginez
```
Target **7/7**.
