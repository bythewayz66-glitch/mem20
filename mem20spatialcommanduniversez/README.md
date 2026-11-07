# mem20spatialcommanduniversez — Spatial Command Universe

First-class mem20 subsystem for spatial command (create_region/add_entity/distance/in_region/spatial_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20autonomousworkcellsz`, `mem20causalroutingbrainz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20faultcontainmentcellsz`, `mem20universalhealthnervoussystemz`.

## Python API (runnable)
```python
from mem20spatialcommanduniversez.domain import create_region, add_entity, distance, spatial_report, probe
r=create_region("r1",[(0,10),(0,10)]); add_entity(r,"e1",(5,5)); print(distance((0,0),(3,4)))  # 5.0
rep=spatial_report(); print(rep["ok"], len(rep["peers"]))  # True 6
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20spatialcommanduniversez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20spatialcommanduniversez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20spatialcommanduniversez serve --port 8834
```
