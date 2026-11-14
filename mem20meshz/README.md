# mem20 Mesh Gold Runtime

Six domain mesh engines are **vendored** under `mem20meshz.meshes`:

- crisis (ex `mem20crisisresponsemeshz`)
- crossdevice (ex `mem20crossdevicememorymeshz`)
- federated (ex `mem20federatedmodellearningmeshz`)
- nearby (ex `mem20nearbydevicemeshz`)
- offline (ex `mem20offlineresiliencemeshz`)
- selfhealing (ex `mem20selfhealingconnectormeshz`)

The old top-level packages are removed after consolidation.

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20meshz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20meshz list
```

## Absorbed: `mem20autonomousrecoverydirectorz`

# mem20autonomousrecoverydirectorz — Autonomous Recovery Director

First-class mem20 subsystem for incident recovery: triage severity/priority, plan rollbacks, apply safe remediations, estimate recovery time, and assess post-recovery health. Real runtime with **6 recovery-specific estate peers** (no generic template), SQLite WAL events, CLI, JSON HTTP API, served cockpit, docs/app integration, and real MCP tools.

## Architecture
`domain.py` (pure ops + `recovery_report`/`probe`/`estate_context`) · `ecosystem.py` (6 adapters, reported-not-fatal) · `runtime.py` (Service + SQLite WAL `EventStore`, CLI, HTTP API, serves `web/`) · `web/` vanilla cockpit · `docs/PLAN.md` · MCP mixin · gateway · docs/app.

## Peers (6, recovery-specific)
| peer | real functions/classes | role |
|---|---|---|
| `mem20faultcontainmentcellsz` | `FaultContainmentCells`, `CircuitOpen` | containment/circuit behavior |
| `mem20selfhealingplansz` | `create_plan`, `plan_status` | healing plan creation/status |
| `mem20universalhealthnervoussystemz` | `register_subsystem`,`check_all`,`overall` | health signals/overall status |
| `mem20pipez` | `version_asset`,`recover`,`vc_health` | versioning and recovery/rollback |
| `mem20eventstreamsuperhighwayz` | `create_stream`,`publish`,`throughput` | incident event publishing |
| `mem20zerotouchnodeswarmz` | `register_node`,`discover`,`quorum` | swarm/node readiness & quorum |

## Python API
```python
from mem20autonomousrecoverydirectorz.domain import (
    triage, rollback_plan, remediate, recovery_time, health_after,
    recovery_report, probe, estate_context,
)

print(triage({"severity": "critical"}))
print(rollback_plan({"version": 2}, {"version": 1}))
print(remediate({}, [{"safe": True}, {"safe": False}]))
print(recovery_time({"severity": "low"}))
print(health_after({"success_rate": 0.8}))

report = recovery_report(incident={"severity": "high", "component": "api"})
print(report["ok"], report["triage"]["priority"], len(report["peers"]))  # 6
print(probe()["ok"])
```

## CLI
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousrecoverydirectorz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousrecoverydirectorz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousrecoverydirectorz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousrecoverydirectorz simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousrecoverydirectorz serve --port 8784
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `POST /api/triage`, `GET /api/events|health`. Cockpit at `/` (served `web/`). State: `~/.mem20/autonomousrecoverydirectorz/state.sqlite3` (SQLite WAL). docs/app: `docs/app/autonomousrecoverydirectorz/index.html` (no Vite edits).

## MCP & registration
`AutonomousRecoveryDirectorToolsMixin` (`mcp/tools/mem20autonomousrecoverydirectorz_tools.py`) in `mcp/server.py`. Gateway `SUBSYSTEMS` entry.

## Tests & conformance
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20autonomousrecoverydirectorz/mem20autonomousrecoverydirectorz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20autonomousrecoverydirectorz
node --check mem20autonomousrecoverydirectorz/mem20autonomousrecoverydirectorz/web/app.js
```
Target **7/7**.

## Limits
Deterministic recovery planning logic; real infrastructure/runbook/orchestrator integrations are target-environment concerns. Peer unavailability surfaced, not fatal.

## Absorbed: `mem20federatedresearchgridz`

# mem20federatedresearchgridz — Federated Research Grid (RM-043, #313)

**Outcome:** split research across nodes and merge results without centralizing all source data.  
**Breakthrough:** large investigations run privately across distributed machines.

Preserves legacy domain API and CAPABILITY Engine/CLI/10-scenario simulator; enriches `search` with federated grid analysis and 6 **unique** peer integrations (different from #300–#312).

## Legacy domain API (preserved)
`register_node(grid,node)`, `distribute_task(grid,task)`, `aggregate_results(results)`, `grid_health(grid)`, `federated_round(grid,task)`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls | Contribution |
|---|---|---|
| `mem20collectivemodelintelligencez` | `ensemble_predict`,`aggregate_confidence`,`diversity_score` | distributed result aggregation/intelligence |
| `mem20personalcognitivesearchz` | `index`,`query`,`recall` | federated/cognitive search & recall |
| `mem20alternativedatabaseplaygroundz` | `query_plan`,`suggest_index`,`benchmark_query` | research query planning/indexing |
| `mem20crdtcollaborationenginez` | `GCounter.increment/value`,`PNCounter` | CRDT merge primitives for distributed state |
| `mem20prioritycollisionresolverz` | `PriorityCollisionResolver.submit/resolve` | task priority/collision resolution |
| `mem20connectormarketplacez` | `ConnectorMarketplace` (+ method call) | research source/connector discovery |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20federatedresearchgridz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20federatedresearchgridz execute '{"query":"federated research","documents":[{"id":"d1","text":"node task"}],"nodes":[{"id":"n1","status":"ready","load":0,"compute":2}],"task":{"cost":1,"size":3}}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20federatedresearchgridz serve --port 8793
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20federatedresearchgridz/tests mem20federatedresearchgridz/mem20federatedresearchgridz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20federatedresearchgridz
```
