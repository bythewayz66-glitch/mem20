# mem20collectivemodelintelligencez — Collective Model Intelligence

First-class mem20 subsystem for collective model intelligence: weighted ensemble prediction, voting, diversity measurement, knowledge distillation loss, and confidence aggregation — with **6 collective-model-specific peers** (unique set), SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app integration, and real MCP tools.

## Peers (6)
`mem20livemodelfusionz` (fuse/weight/select/best/vote), `mem20loreragcontentgeneratorz` (generation quality), `mem20capabilitymarketplacez` (model routing), `mem20eventstreamsuperhighwayz` (ensemble events), `mem20universalhealthnervoussystemz` (model health), `mem20causalroutingbrainz` (causal route scoring). Failures reported, not fatal.

## Python API (runnable)
```python
from mem20collectivemodelintelligencez.domain import ensemble_predict, diversity_score, knowledge_distill, aggregate_confidence, collective_report, probe, estate_context
print(ensemble_predict([1,2,3]))           # 2.0
print(ensemble_predict(["a","a","b"]))     # a
print(diversity_score([1,1,2]))            # 0.3333
print(knowledge_distill([1,0],[0.9,0.1]))  # ~0.01
print(aggregate_confidence([0.8,0.6]))     # 0.7
r = collective_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"], estate_context()["peer_count"])      # True 6
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20collectivemodelintelligencez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20collectivemodelintelligencez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20collectivemodelintelligencez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20collectivemodelintelligencez simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20collectivemodelintelligencez serve --port 8790
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit at `/`. State `~/.mem20/collectivemodelintelligencez/state.sqlite3` (WAL). docs/app: `docs/app/collectivemodelintelligencez/index.html` (no Vite edits).

## MCP & registration
`CollectiveModelIntelligenceToolsMixin` in `mcp/server.py`. Gateway `SUBSYSTEMS` entry.

## Tests & conformance
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20collectivemodelintelligencez/mem20collectivemodelintelligencez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20collectivemodelintelligencez
```
Target **7/7**.
