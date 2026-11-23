# mem20runtimecompatibilityenginez — Runtime Compatibility Engine

First-class mem20 subsystem for runtime compatibility checking (Python/deps compatibility, reports, fix suggestions) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20deterministicconfigurationgraphz`, `mem20capabilitymarketplacez`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20selfhealingplansz`, `mem20devicecapabilitycompilerz`.

## Python API (runnable)
```python
from mem20runtimecompatibilityenginez.domain import check_python, check_deps, compatibility_report, suggest_fixes, runtime_report, probe
print(check_python((3,1)))  # True
print(check_deps(["a"],["a"])["ok"])  # True
r=runtime_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20runtimecompatibilityenginez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20runtimecompatibilityenginez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20runtimecompatibilityenginez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20runtimecompatibilityenginez serve --port 8821
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/runtimecompatibilityenginez/index.html` (no Vite edits).

## MCP & registration
`RuntimeCompatibilityEngineToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20runtimecompatibilityenginez/mem20runtimecompatibilityenginez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20runtimecompatibilityenginez
```
Target **7/7**.
