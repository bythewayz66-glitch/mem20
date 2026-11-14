# mem20realtimeteampresencez — Real-Time Team Presence

First-class mem20 subsystem for real-time team presence (set/get presence, online/away users, presence health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20universalhealthnervoussystemz`, `mem20faultcontainmentcellsz`, `mem20selfhealingplansz`, `mem20mixedinitiativefocusenginez`.

## Python API (runnable)
```python
from mem20realtimeteampresencez.domain import set_presence, get_presence, online_users, presence_report, probe
p={}; set_presence(p,"alice","online"); print(get_presence(p,"alice")["status"])  # online
print(online_users(p))  # ['alice']
r=presence_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeteampresencez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeteampresencez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeteampresencez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeteampresencez serve --port 8813
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/realtimeteampresencez/index.html` (no Vite edits).

## MCP & registration
`RealTimeTeamPresenceToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20realtimeteampresencez/mem20realtimeteampresencez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20realtimeteampresencez
```
Target **7/7**.
