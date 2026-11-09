# mem20predictiverecallenginez — Predictive Recall Engine

First-class mem20 subsystem for predictive recall (predict next items, recall scoring, prefetch, cache hit rate) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20causalroutingbrainz`, `mem20contextcompressionforgez`, `mem20eventstreamsuperhighwayz`, `mem20mixedinitiativefocusenginez`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## Python API (runnable)
```python
from mem20predictiverecallenginez.domain import predict_next, recall_score, prefetch, cache_hit_rate, recall_report, probe
print(predict_next(["a","b","a"],["a","b","c"])[0])  # a
print(prefetch([1,2,3],2))  # [1,2]
print(cache_hit_rate(1,4))  # 0.25
r=recall_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20predictiverecallenginez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20predictiverecallenginez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20predictiverecallenginez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20predictiverecallenginez serve --port 8806
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/predictiverecallenginez/index.html` (no Vite edits).

## MCP & registration
`PredictiveRecallEngineToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20predictiverecallenginez/mem20predictiverecallenginez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20predictiverecallenginez
```
Target **7/7**.
