# mem20selfoptimizingkernelz — Self-Optimizing Kernel

First-class mem20 subsystem for self-optimizing kernels (parameter optimization, scoring, search) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20causalroutingbrainz`, `mem20demandforecastandcapacitybrainz`, `mem20counterfactualmemorysimulatorz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20faultcontainmentcellsz`.

## Python API (runnable)
```python
from mem20selfoptimizingkernelz.domain import optimize, score, search, kernel_report, probe
print(optimize({"a":0},{"a":10},0.5)["a"])  # 5.0
print(score({"a":2},{"a":3}))  # 6
r=kernel_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfoptimizingkernelz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfoptimizingkernelz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfoptimizingkernelz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfoptimizingkernelz serve --port 8826
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/selfoptimizingkernelz/index.html` (no Vite edits).

## MCP & registration
`SelfOptimizingKernelToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20selfoptimizingkernelz/mem20selfoptimizingkernelz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20selfoptimizingkernelz
```
Target **7/7**.
