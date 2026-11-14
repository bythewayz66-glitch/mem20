# mem20crossplatformmicrokernelz — Cross-Platform Microkernel

First-class mem20 subsystem for cross-platform microkernel primitives (process lifecycle, memory pages, IPC, priority scheduling, context switch) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app, and real MCP tools.

## Peers (6)
`mem20zerotouchnodeswarmz`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20universalhealthnervoussystemz`, `mem20capabilitymarketplacez`, `mem20datalocalityoptimizerz`.

## Python API (runnable)
```python
from mem20crossplatformmicrokernelz.domain import create_process, allocate_memory, ipc_send, schedule, context_switch, kill, microkernel_report, probe
p1=create_process("p1",1); allocate_memory(p1,[1,2]); p2=create_process("p2",0)
print(schedule([p2,p1])[0]["pid"])  # p1
print(ipc_send("p1","p2","hi")["delivered"])  # True
print(kill(p2)["state"])  # terminated
r=microkernel_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20crossplatformmicrokernelz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20crossplatformmicrokernelz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20crossplatformmicrokernelz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20crossplatformmicrokernelz serve --port 8795
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/crossplatformmicrokernelz/index.html` (no Vite edits).

## MCP & registration
`CrossPlatformMicrokernelToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20crossplatformmicrokernelz/mem20crossplatformmicrokernelz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20crossplatformmicrokernelz
```
Target **7/7**.
