# mem20realworldimpactrewardsz — Real-World Impact Rewards

First-class mem20 subsystem for real-world impact rewards (record impact, compute rewards, leaderboards) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20dynamicquestrewardcomposerz`, `mem20crossproductloyaltygraphz`, `mem20customerlifecycleenginez`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20demandforecastandcapacitybrainz`.

## Python API (runnable)
```python
from mem20realworldimpactrewardsz.domain import record_impact, compute_reward, leaderboard, impact_report, probe
i={}; record_impact(i,"alice","cleanup",2.0); print(compute_reward(i,"alice"))  # 2.0
print(leaderboard(i)[0]["user"])  # alice
r=impact_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realworldimpactrewardsz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realworldimpactrewardsz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realworldimpactrewardsz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realworldimpactrewardsz serve --port 8814
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/realworldimpactrewardsz/index.html` (no Vite edits).

## MCP & registration
`RealWorldImpactRewardsToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20realworldimpactrewardsz/mem20realworldimpactrewardsz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20realworldimpactrewardsz
```
Target **7/7**.
