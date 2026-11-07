# mem20playermotivationtwinz — Player Motivation Twin

First-class mem20 subsystem for player motivation twins (motivation over time, events/updates, churn prediction, motivation segments, twin health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20customerlifecycleenginez`, `mem20dynamicquestrewardcomposerz`, `mem20communitychallengeenginez`, `mem20counterfactualmemorysimulatorz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20playermotivationtwinz.domain import create_twin, update, predict_churn, motivation_segments, twin_health, motivation_report, probe
t=create_twin("p1"); update(t,{"delta":0.3}); print(motivation_segments(t))  # high
print(predict_churn({"motivation":0.1}))  # True
r=motivation_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20playermotivationtwinz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20playermotivationtwinz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20playermotivationtwinz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20playermotivationtwinz serve --port 8805
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/playermotivationtwinz/index.html` (no Vite edits).

## MCP & registration
`PlayerMotivationTwinToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20playermotivationtwinz/mem20playermotivationtwinz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20playermotivationtwinz
```
Target **7/7**.
