# mem20communitychallengeenginez — Community Challenge Engine

First-class mem20 subsystem for community challenges (create/join, progress recording, leaderboards, completion, reward pools) with **6 community-challenge-specific peers**, SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app integration, and real MCP tools.

## Peers (6)
`mem20dynamicquestrewardcomposerz` (quest/reward composition), `mem20eventstreamsuperhighwayz` (challenge events), `mem20crossproductloyaltygraphz` (loyalty/graph), `mem20autonomoussaleslaboratoryz` (engagement signals), `mem20capabilitymarketplacez` (reward routing), `mem20customerlifecycleenginez` (lifecycle/retention).

## Python API (runnable)
```python
from mem20communitychallengeenginez.domain import create_challenge, join, record_progress, leaderboard, check_completion, reward_pool, challenge_report, probe
c = create_challenge("weekly", 10); join(c,"u1"); record_progress(c,"u1",10)
print(check_completion(c)["completed"])  # True
print(leaderboard(c)[0]["user"])         # u1
print("u1" in reward_pool(c, 100))      # True
r = challenge_report(); print(r["ok"], len(r["peers"]))  # 6
print(probe()["ok"])                     # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20communitychallengeenginez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20communitychallengeenginez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20communitychallengeenginez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20communitychallengeenginez serve --port 8791
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/communitychallengeenginez/index.html` (no Vite edits). State WAL `~/.mem20/communitychallengeenginez/state.sqlite3`.

## MCP & registration
`CommunityChallengeEngineToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS` entry.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20communitychallengeenginez/mem20communitychallengeenginez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20communitychallengeenginez
```
Target **7/7**.
