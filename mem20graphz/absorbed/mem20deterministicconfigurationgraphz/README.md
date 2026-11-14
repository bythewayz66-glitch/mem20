# mem20deterministicconfigurationgraphz — Deterministic Configuration Graph

First-class mem20 subsystem for deterministic configuration graphs (nodes/edges, dependency resolution, validation/cycle detection, config diff) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20selfhealingplansz`, `mem20universalhealthnervoussystemz`, `mem20zerotouchnodeswarmz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20deterministicconfigurationgraphz.domain import add_node, add_edge, resolve, validate, diff_configs, config_report, probe
g={}; add_node(g,"p",{"a":1}); add_node(g,"c",{"b":2}); add_edge(g,"p","c")
print(resolve(g,"c"))  # {'a': 1, 'b': 2}
print(validate(g)["valid"])  # True
print("x" in diff_configs({"x":1},{"x":2}))  # True
r=config_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20deterministicconfigurationgraphz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20deterministicconfigurationgraphz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20deterministicconfigurationgraphz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20deterministicconfigurationgraphz serve --port 8800
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/deterministicconfigurationgraphz/index.html` (no Vite edits).

## MCP & registration
`DeterministicConfigurationGraphToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20deterministicconfigurationgraphz/mem20deterministicconfigurationgraphz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20deterministicconfigurationgraphz
```
Target **7/7**.
