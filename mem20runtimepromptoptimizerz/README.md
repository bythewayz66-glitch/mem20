# mem20runtimepromptoptimizerz — Runtime Prompt Optimizer

First-class mem20 subsystem for runtime prompt optimization (tokenize, compress, score, optimize, prompt health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20contextcompressionforgez`, `mem20causalroutingbrainz`, `mem20capabilitymarketplacez`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20causalroutingbrainz`.

## Python API (runnable)
```python
from mem20runtimepromptoptimizerz.domain import tokenize, compress, score_prompt, optimize, prompt_report, probe
print(tokenize("a b"))  # ['a', 'b']
print(score_prompt("hello world",{"hello":1}))  # 1.0
r=prompt_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20runtimepromptoptimizerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20runtimepromptoptimizerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20runtimepromptoptimizerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20runtimepromptoptimizerz serve --port 8822
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/runtimepromptoptimizerz/index.html` (no Vite edits).

## MCP & registration
`RuntimePromptOptimizerToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20runtimepromptoptimizerz/mem20runtimepromptoptimizerz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20runtimepromptoptimizerz
```
Target **7/7**.
