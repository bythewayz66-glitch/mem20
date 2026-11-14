# mem20skillmemorytransferz — Skill Memory Transfer

First-class mem20 subsystem for skill memory transfer (extract/transfer/merge_skills/transfer_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20dynamicskillgraphz`, `mem20episodicmemorygraphz`, `mem20memorytimemachinez`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20faultcontainmentcellsz`.

## Python API (runnable)
```python
from mem20skillmemorytransferz.domain import transfer, transfer_report, probe
src={"skills":{"s1":{"w":1}}}; dst={}; print(transfer(src,dst,"s1")["ok"])  # True
r=transfer_report(); print(r["ok"], len(r["peers"]))  # True 6
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20skillmemorytransferz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20skillmemorytransferz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20skillmemorytransferz serve --port 8833
```

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20skillmemorytransferz/mem20skillmemorytransferz/tests -q --noconftest -p no:cacheprovider
```
