# mem20dynamicskillgraphz — Dynamic Skill Graph

First-class mem20 subsystem for dynamic skill graphs (skills, prerequisites, proficiency, learning paths, skill gaps, stats) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20capabilitymarketplacez`, `mem20dynamicquestrewardcomposerz`, `mem20customerlifecycleenginez`, `mem20eventstreamsuperhighwayz`, `mem20causalroutingbrainz`, `mem20rewardforgez`.

## Python API (runnable)
```python
from mem20dynamicskillgraphz.domain import add_skill, update_proficiency, learning_path, skill_gap, graph_stats, skill_report, probe
g={}; add_skill(g,"a"); add_skill(g,"b",["a"]); update_proficiency(g,"a",0.8)
print(learning_path(g,"b"))  # ['a', 'b']
print(skill_gap(g,["a"])[0]["gap"])  # 0.2
r=skill_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicskillgraphz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicskillgraphz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicskillgraphz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicskillgraphz serve --port 8804
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/dynamicskillgraphz/index.html` (no Vite edits).

## MCP & registration
`DynamicSkillGraphToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20dynamicskillgraphz/mem20dynamicskillgraphz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20dynamicskillgraphz
```
Target **7/7**.
