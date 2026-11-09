# mem20selftuningresourcegovernorz — Self-Tuning Resource Governor

First-class mem20 subsystem for self-tuning resource governance (govern/adjust_quota/governor_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20causalroutingbrainz`, `mem20causalroutingbrainz`, `mem20faultcontainmentcellsz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20autonomousrecoverydirectorz`.

## Python API (runnable)
```python
from mem20selftuningresourcegovernorz.domain import govern, adjust_quota, governor_report, probe
print(govern({"c":100},{"c":90},{"c":0.8})[0]["action"])  # throttle
print(adjust_quota("c",100,0.9))  # 120.0
r=governor_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selftuningresourcegovernorz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selftuningresourcegovernorz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selftuningresourcegovernorz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selftuningresourcegovernorz serve --port 8827
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/selftuningresourcegovernorz/index.html` (no Vite edits).

## MCP & registration
`SelfTuningResourceGovernorToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20selftuningresourcegovernorz/mem20selftuningresourcegovernorz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20selftuningresourcegovernorz
```
Target **7/7**.
