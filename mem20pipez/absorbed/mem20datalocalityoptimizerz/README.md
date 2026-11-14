# mem20datalocalityoptimizerz — Data Locality Optimizer

First-class mem20 subsystem for data locality optimization (placement scoring, optimal placement, migration cost, locality reporting, rebalance) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20zerotouchnodeswarmz`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20universalhealthnervoussystemz`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## Python API (runnable)
```python
from mem20datalocalityoptimizerz.domain import placement_score, optimal_placement, migration_cost, locality_report, rebalance, placement_report, probe
nodes=[{"id":"n1","latency_ms":1,"capacity_gb":10,"used_gb":0},{"id":"n2","latency_ms":20,"capacity_gb":10,"used_gb":0}]
print(optimal_placement({"size_gb":1}, [dict(n) for n in nodes])["id"])  # n1
print(migration_cost({"size_gb":10},{"egress_cost":0.1},{})==1.0)  # True
print(locality_report([{"local":True},{"local":False}])["ratio"])  # 0.5
r=placement_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20datalocalityoptimizerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20datalocalityoptimizerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20datalocalityoptimizerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20datalocalityoptimizerz serve --port 8799
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/datalocalityoptimizerz/index.html` (no Vite edits).

## MCP & registration
`DataLocalityOptimizerToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20datalocalityoptimizerz/mem20datalocalityoptimizerz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20datalocalityoptimizerz
```
Target **7/7**.
