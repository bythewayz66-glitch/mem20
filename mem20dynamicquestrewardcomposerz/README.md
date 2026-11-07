# mem20dynamicquestrewardcomposerz — Dynamic Quest Reward Composer

First-class mem20 subsystem for dynamic quest and reward composition (quest generation, reward scaling, balancing, quest chains, completion rate) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20communitychallengeenginez`, `mem20dynamicnarrativeenginez`, `mem20eventstreamsuperhighwayz`, `mem20crossproductloyaltygraphz`, `mem20capabilitymarketplacez`, `mem20customerlifecycleenginez`.

## Python API (runnable)
```python
from mem20dynamicquestrewardcomposerz.domain import generate_quest, reward_for_quest, balance_quests, quest_chain, completion_rate, quest_report, probe
q=generate_quest(2,seed=1); print(q["difficulty"])  # 2
print(reward_for_quest(q,1)["xp"]>0)  # True
print(quest_chain([{"difficulty":2},{"difficulty":1}])[0]["difficulty"])  # 1
r=quest_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicquestrewardcomposerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicquestrewardcomposerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicquestrewardcomposerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicquestrewardcomposerz serve --port 8803
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/dynamicquestrewardcomposerz/index.html` (no Vite edits).

## MCP & registration
`DynamicQuestRewardComposerToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20dynamicquestrewardcomposerz/mem20dynamicquestrewardcomposerz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20dynamicquestrewardcomposerz
```
Target **7/7**.
