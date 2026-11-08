# mem20speculativeworkflowenginez — Speculative Workflow Engine

First-class mem20 subsystem for speculative workflows (speculate/commit/rollback/speculative_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20counterfactualmemorysimulatorz`, `mem20causalroutingbrainz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20faultcontainmentcellsz`, `mem20selfhealingplansz`.

## Python API (runnable)
```python
from mem20speculativeworkflowenginez.domain import speculate, commit, rollback, speculative_report, probe
r=speculate({},["b1","b2"]); commit(r,"b1"); print(speculative_report()["ok"])  # True
```
