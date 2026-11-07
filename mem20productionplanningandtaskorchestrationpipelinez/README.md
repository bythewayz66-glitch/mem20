# mem20productionplanningandtaskorchestrationpipelinez — Production Planning and Task Orchestration Pipeline

First-class mem20 subsystem for production planning and task orchestration (capacity-aware planning, agent assignment, bottleneck detection, pipeline health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20autonomousworkcellsz`, `mem20zerotouchnodeswarmz`, `mem20demandforecastandcapacitybrainz`, `mem20faultcontainmentcellsz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20productionplanningandtaskorchestrationpipelinez.domain import create_plan, orchestrate, bottleneck, pipeline_health, orchestration_report, probe
p=create_plan([{"id":"a","effort":2,"priority":1}], capacity=5); print(p["capacity_used"])  # 2
print(orchestrate([{"id":"t1"}],["ag1"])[0]["agent"])  # ag1
print(bottleneck([{"id":"b","effort":5},{"id":"a","effort":1}])["id"])  # b
r=orchestration_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20productionplanningandtaskorchestrationpipelinez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20productionplanningandtaskorchestrationpipelinez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20productionplanningandtaskorchestrationpipelinez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20productionplanningandtaskorchestrationpipelinez serve --port 8807
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/productionplanningandtaskorchestrationpipelinez/index.html` (no Vite edits).

## MCP & registration
`ProductionPlanningAndTaskOrchestrationPipelineToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20productionplanningandtaskorchestrationpipelinez/mem20productionplanningandtaskorchestrationpipelinez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20productionplanningandtaskorchestrationpipelinez
```
Target **7/7**.
