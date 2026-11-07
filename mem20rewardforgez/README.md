# mem20rewardforgez — Reward Forge

First-class mem20 subsystem for reward forging (linear rewards, shaping, normalization, reward health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20dynamicquestrewardcomposerz`, `mem20realworldimpactrewardsz`, `mem20counterfactualmemorysimulatorz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## Python API (runnable)
```python
from mem20rewardforgez.domain import linear_reward, shaped_reward, normalize, forge_report, probe
print(linear_reward({"a":2},{"a":3}))  # 6
print(shaped_reward(1,0.5))  # 1.5
print(normalize([0,10]))  # [0.0, 1.0]
r=forge_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20rewardforgez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20rewardforgez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20rewardforgez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20rewardforgez serve --port 8818
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/rewardforgez/index.html` (no Vite edits).

## MCP & registration
`RewardForgeToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20rewardforgez/mem20rewardforgez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20rewardforgez
```
Target **7/7**.
