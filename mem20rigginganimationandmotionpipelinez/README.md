# mem20rigginganimationandmotionpipelinez — Rigging, Animation and Motion Pipeline

First-class mem20 subsystem for rigging, animation and motion pipeline (rig creation, posing, animation frames, motion blending) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20devicecapabilitycompilerz`, `mem20datalocalityoptimizerz`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20capabilitymarketplacez`, `mem20deterministicconfigurationgraphz`.

## Python API (runnable)
```python
from mem20rigginganimationandmotionpipelinez.domain import create_rig, set_pose, animate, motion_blend, rig_report, probe
r=create_rig(["arm"]); set_pose(r,"arm",(1,0,0)); print(r["pose"]["arm"])  # (1, 0, 0)
print(motion_blend({"a":(10,0,0)},{"a":(0,0,0)},0.5)["a"][0])  # 5.0
rep=rig_report(); print(rep["ok"], len(rep["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20rigginganimationandmotionpipelinez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20rigginganimationandmotionpipelinez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20rigginganimationandmotionpipelinez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20rigginganimationandmotionpipelinez serve --port 8819
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/rigginganimationandmotionpipelinez/index.html` (no Vite edits).

## MCP & registration
`RiggingAnimationAndMotionPipelineToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20rigginganimationandmotionpipelinez/mem20rigginganimationandmotionpipelinez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20rigginganimationandmotionpipelinez
```
Target **7/7**.
