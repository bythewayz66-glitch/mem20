# mem20realitytosoftwarecompilerz — Reality-to-Software Compiler

First-class mem20 subsystem for compiling real-world specs to software (ingest, compile, validate, diff, health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20autonomoussoftwarefoundryz`, `mem20deterministicconfigurationgraphz`, `mem20eventstreamsuperhighwayz`, `mem20causalroutingbrainz`, `mem20faultcontainmentcellsz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20realitytosoftwarecompilerz.domain import ingest, compile_to_code, validate_spec, diff_spec, compiler_report, probe
s=ingest("name: demo"); print(s["name"])  # demo
print("Demo" in compile_to_code({"name":"demo"}))  # True
print(validate_spec({"name":"x"})["valid"])  # True
r=compiler_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realitytosoftwarecompilerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realitytosoftwarecompilerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realitytosoftwarecompilerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realitytosoftwarecompilerz serve --port 8810
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/realitytosoftwarecompilerz/index.html` (no Vite edits).

## MCP & registration
`RealityToSoftwareCompilerToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20realitytosoftwarecompilerz/mem20realitytosoftwarecompilerz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20realitytosoftwarecompilerz
```
Target **7/7**.
