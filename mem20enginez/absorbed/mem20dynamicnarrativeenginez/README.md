# mem20dynamicnarrativeenginez — Dynamic Narrative Engine

First-class mem20 subsystem for dynamic narrative engines (story graph, branching choices, state tracking) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20eventstreamsuperhighwayz`, `mem20communitychallengeenginez`, `mem20rewardforgez`, `mem20mixedinitiativefocusenginez`, `mem20capabilitymarketplacez`, `mem20simz`.

## Python API (runnable)
```python
from mem20dynamicnarrativeenginez.domain import create_story, add_node, choose, current_text, narrative_state, narrative_report, probe
s=create_story("a"); add_node(s,"a","hi",[{"label":"go","target":"b"}]); add_node(s,"b","end")
choose(s,0); print(current_text(s))  # end
print(narrative_state(s)["visited"])  # 1
r=narrative_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicnarrativeenginez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicnarrativeenginez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicnarrativeenginez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicnarrativeenginez serve --port 8802
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/dynamicnarrativeenginez/index.html` (no Vite edits).

## MCP & registration
`DynamicNarrativeEngineToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20dynamicnarrativeenginez/mem20dynamicnarrativeenginez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20dynamicnarrativeenginez
```
Target **7/7**.
