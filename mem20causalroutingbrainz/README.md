# mem20causalroutingbrainz — Causal Routing Brain

First-class mem20 subsystem for causal routing decisions (average treatment effect, weighted causal routing scores, confounder adjustment, intervention value, causal graph construction) with **6 causal-routing-specific estate peers** (unique set), SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app integration, and real MCP tools.

## Peers (6)
`mem20counterfactualmemorysimulatorz` (counterfactual/compare/outcome_probability), `mem20eventstreamsuperhighwayz` (route events), `mem20capabilitymarketplacez` (route target capability), `mem20faultcontainmentcellsz` (failure/containment signal), `mem20universalhealthnervoussystemz` (health-aware routing), `mem20zerotouchnodeswarmz` (node targets/quorum). Failures reported, not fatal.

## Python API (runnable)
```python
from mem20causalroutingbrainz.domain import (
    causal_effect, route_by_cause, confounder_adjust, intervention_value, causal_graph,
    routing_report, probe, estate_context,
)
print(causal_effect([1,1],[0,0]))                    # 1.0
print(route_by_cause({"a":1.0},{"a":2.0}))           # 2.0
print(confounder_adjust(1.0,0.2))                     # 0.8
print(intervention_value(1.0,1.5))                    # 0.5
print("a" in causal_graph([("a","b")]))               # True
report = routing_report()
print(report["ok"], len(report["peers"]))             # True, 6
print(probe()["ok"], estate_context()["peer_count"])  # True 6
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20causalroutingbrainz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20causalroutingbrainz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20causalroutingbrainz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20causalroutingbrainz simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20causalroutingbrainz serve --port 8789
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit at `/` (served). State `~/.mem20/causalroutingbrainz/state.sqlite3` (WAL) or `--store`/`MEM20_CAUSALROUTE_STORE`. docs/app: `docs/app/causalroutingbrainz/index.html` (no Vite edits).

## MCP & registration
`CausalRoutingBrainToolsMixin` (`mcp/tools/mem20causalroutingbrainz_tools.py`) in `mcp/server.py` (`causalroutingbrainz_status|doctor`). Gateway `SUBSYSTEMS` entry.

## Tests & conformance
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20causalroutingbrainz/mem20causalroutingbrainz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20causalroutingbrainz
```
Target **7/7**. Peer unavailability surfaced, not fatal.
