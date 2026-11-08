# mem20specialistmodelforgez — Specialist Model Forge

First-class mem20 subsystem for specialist model forging (forge/evaluate/merge_specialists/forge_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20collectivemodelintelligencez`, `mem20causalroutingbrainz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20faultcontainmentcellsz`, `mem20autonomoussoftwarefoundryz`.

## Python API (runnable)
```python
from mem20specialistmodelforgez.domain import forge, evaluate, merge_specialists, forge_report, probe
m=forge("base","code",["d1"],seed=1); print(0<=evaluate(m,["t"])<=1)  # True
r=forge_report(); print(r["ok"], len(r["peers"]))  # True 6
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20specialistmodelforgez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20specialistmodelforgez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20specialistmodelforgez serve --port 8835
```
