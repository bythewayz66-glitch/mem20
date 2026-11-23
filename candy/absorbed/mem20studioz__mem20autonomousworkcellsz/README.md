# mem20autonomousworkcellsz — Autonomous Workcells

First-class mem20 subsystem for autonomous work cells: bounded task queues, worker assignment, throughput tracking, and cell health — backed by **6 workcell-specific estate peers** (no generic template), a SQLite WAL event log, a CLI, a JSON HTTP API, a served operator cockpit, docs/app estate integration, and real MCP tools.

## At a glance

| item | value |
|---|---|
| package | `mem20autonomousworkcellsz` |
| console entry | `mem20autonomousworkcellsz` / `python -m mem20autonomousworkcellsz` |
| core modules | `domain.py`, `ecosystem.py`, `runtime.py` |
| web cockpit | `web/index.html`, `web/style.css`, `web/app.js` (served, no build step) |
| state | SQLite WAL `events` (`~/.mem20/autonomousworkcellsz/state.sqlite3` or `--store` / `MEM20_WORKCELLS_STORE`) |
| cross-subsystem peers | 6, called with real APIs on report/probe; failures reported, never fatal |
| registrations | gateway `SUBSYSTEMS`, MCP mixin wired in `mcp/server.py`, `docs/app/autonomousworkcellsz/` linked from `docs/app/README.md` |
| conformance target | 7/7 |

## Architecture

- `domain.py` — pure workcell ops (`create_cell`, `enqueue`, `assign_workers`, `process_next`, `throughput`, `cell_health`) plus `workcell_report()`, `probe()`, `estate_context()`.
- `ecosystem.py` — 6 peer adapters (bootstraps peer package paths). Adapters return computed results or `{"ok": false, "error": ...}`; core ops do not crash on peer unavailability.
- `runtime.py` — `Service` + SQLite WAL `EventStore`; argparse CLI; `ThreadingHTTPServer` JSON API serving static `web/` (path-traversal protection, CORS).
- `web/` — vanilla cockpit (no compiled assets). `docs/PLAN.md` — delivery record. `docs/app/autonomousworkcellsz/index.html` — estate monitor (static; no Vite edits).

## Domain model

| function | behavior |
|---|---|
| `create_cell(name, capacity=4)` | new cell with queue/workers/completed counters |
| `enqueue(cell, task)` / `assign_workers(cell, workers)` | append work; cap workers to `capacity` |
| `process_next(cell)` | pop next task, assign round-robin over workers, increment `completed`; returns `{task, worker}` or `None` |
| `throughput(cell, window_s=60)` | completed-per-minute over a window |
| `cell_health(cell)` | `queue_depth`, `utilization` (capped at 1.0), `completed` |
| `workcell_report(cell=None, tasks=None)` | runs a small cell scenario, computes health/throughput, and aggregates 6 peer judgements |
| `probe()` / `estate_context()` | peer reachability and estate summary |

## Ecosystem peers (6, workcell-specific)

Chosen for autonomous workcell execution (worker placement, routing, telemetry, isolation, prioritization, capacity). This 6-peer combination is unique to this subsystem.

| peer | real functions/classes used | role |
|---|---|---|
| `mem20zerotouchnodeswarmz` | `register_node`, `discover`, `quorum`, `assign_task` | discover ready workers/nodes, establish quorum, assign a task |
| `mem20capabilitymarketplacez` | `CapabilityMarketplace`, `add`, `locate`, `distribution` | route work by capability via consistent hashing |
| `mem20eventstreamsuperhighwayz` | `create_stream`, `publish`, `throughput` | publish workcell events and report stream throughput |
| `mem20faultcontainmentcellsz` | `FaultContainmentCells`, `CircuitOpen`, `call` | isolate cell execution behind a circuit breaker (open reported, not fatal) |
| `mem20mixedinitiativefocusenginez` | `focus_score`, `focus_health`, `take_over`, `suggest` | prioritize/focus work; indicate takeover and suggestions |
| `mem20causalroutingbrainz` | `DemandForecastAndCapacityBrain` (`observe`/`forecast`/`capacity_for`) | forecast load and compute headroom vs cell capacity |

## Python API (runnable)

```python
from mem20autonomousworkcellsz.domain import (
    assign_workers, cell_health, create_cell, enqueue, estate_context,
    process_next, probe, throughput, workcell_report,
)

cell = create_cell("a", capacity=4)
enqueue(cell, {"id": 1, "capability": "cpu"})
enqueue(cell, {"id": 2, "capability": "io"})
assign_workers(cell, ["w1", "w2"])
result = process_next(cell)
print(result["worker"], result["task"]["id"])   # w1 1
print(cell_health(cell)["completed"])            # 1
print(throughput({"completed": 60}, 60))         # 60.0

report = workcell_report()
print(report["ok"], report["processed"], len(report["peers"]))  # 6 peers
print(probe()["ok"], estate_context()["peer_count"])            # True 6
```

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousworkcellsz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousworkcellsz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousworkcellsz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousworkcellsz simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousworkcellsz serve --port 8787
```

`--store PATH` or `MEM20_WORKCELLS_STORE` selects the SQLite state file.

## HTTP API and web/docs

| method | route | purpose |
|---|---|---|
| GET | `/api/health` | service health |
| GET/POST | `/api/status` | workcell report (POST accepts `cell`, `tasks`) |
| GET/POST | `/api/doctor` | peer probe |
| POST | `/api/simulate` | internal scenarios |
| GET | `/api/events?since=&limit=` | WAL events |

```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousworkcellsz serve --port 8787
# cockpit:        http://127.0.0.1:8787/
# estate monitor: docs/app/autonomousworkcellsz/index.html (no Vite assets edited)
```

## MCP and registration

- `AutonomousWorkcellsToolsMixin` (`mcp/tools/mem20autonomousworkcellsz_tools.py`) wired in `mcp/server.py`: `autonomousworkcellsz_status`, `autonomousworkcellsz_doctor` (lazy/guarded).
- Gateway: `gateway/mem20_gateway.py` `SUBSYSTEMS["mem20autonomousworkcellsz"]` (purpose, entry, owner, wave).
- docs/app linked from `docs/app/README.md`.

## Tests and conformance

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20autonomousworkcellsz/mem20autonomousworkcellsz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20autonomousworkcellsz
node --check mem20autonomousworkcellsz/mem20autonomousworkcellsz/web/app.js
```

Target: **7/7** (real domain, no stubs, real-value tests, CLI, runnable README, >=5 cross-module imports+calls on covered lines, MCP/gateway registration).

## Limits

- Queue/throughput logic is deterministic and in-process; distributed durable queues, real worker runtimes, and production orchestrators are target-environment integrations.
- Peer unavailability is surfaced in report/probe/doctor/MCP, not swallowed and not fatal to core cell operations.
