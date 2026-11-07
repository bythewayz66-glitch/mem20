# mem20counterfactualmemorysimulatorz — Counterfactual Memory Simulator

First-class mem20 subsystem for counterfactual memory simulation (branch, replay, counterfactual, compare, outcome probability) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app, and real MCP tools.

## Peers (6)
`mem20causalroutingbrainz`, `mem20eventstreamsuperhighwayz`, `mem20autonomousrecoverydirectorz`, `mem20selfhealingplansz`, `mem20demandforecastandcapacitybrainz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20counterfactualmemorysimulatorz.domain import branch, replay, counterfactual, compare, outcome_probability, counterfactual_report, probe
b=branch({"state":{"a":1},"branch":0},{"b":2}); print(b["branch"])  # 1
print(len(replay({"state":{"a":1}},[{"a":2},{"a":3}])))             # 3
cf=counterfactual({"state":{"a":1}},{"change":{"a":2}}); print(cf["state"]["a"])  # 2
print("a" in compare({"state":{"a":1}},{"state":{"a":2}}))          # True
print(outcome_probability({"base_rate":0.5},{"effect":0.2}))         # 0.7
r=counterfactual_report(); print(r["ok"], len(r["peers"]))          # True 6
print(probe()["ok"])                                                 # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20counterfactualmemorysimulatorz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20counterfactualmemorysimulatorz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20counterfactualmemorysimulatorz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20counterfactualmemorysimulatorz serve --port 8794
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/counterfactualmemorysimulatorz/index.html` (no Vite edits).

## MCP & registration
`CounterfactualMemorySimulatorToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20counterfactualmemorysimulatorz/mem20counterfactualmemorysimulatorz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20counterfactualmemorysimulatorz
```
Target **7/7**.
