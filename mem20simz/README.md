# mem20simz — Simz (Simulator Runtime)

Unified simulation subsystem consolidating all simulator/simulation runtimes under `mem20simz/sims/`. First-class mem20 crew runtime for simulators with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core APIs preserved (`estate_context` superset, `MEMBERS`/`__version__`, legacy `--members/--version`).

## Peers (6)
`mem20simz`, `mem20twinz`, `mem20causalroutingbrainz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20faultcontainmentcellsz`.

## Python API (runnable)
```python
from mem20simz.domain import sim_report, probe, estate_context
r=sim_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20simz --members
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20simz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20simz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20simz serve --port 8831
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/simz/index.html`.

## MCP & registration
`SimzToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20simz -q --noconftest -p no:cacheprovider
```
Target **7/7**.

## Absorbed: `mem20capabilitymarketplacez`

# mem20capabilitymarketplacez — Capability Marketplace

Consistent-hashing capability routing with virtual nodes, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20capabilitymarketplacez.domain import CapabilityMarketplace, estate_context

m = CapabilityMarketplace(replicas=64)
for c in ("alpha", "beta", "gamma"):
    m.add(c)
print(m.locate("my-key"))
print(dict(m.distribution(500)))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20capabilitymarketplacez --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20capabilitymarketplacez/mem20capabilitymarketplacez/tests -q
```

## Absorbed: `mem20causalroutingbrainz`

# mem20causalroutingbrainz — Causal Routing Brain (Unified)

Unified brain subsystem consolidating brain/forecast/fleet/migration/progression runtimes under `mem20causalroutingbrainz/brains/`.

First-class mem20 subsystem for causal routing decisions (average treatment effect, weighted causal routing scores, confounder adjustment, intervention value, causal graph construction) with **6 causal-routing-specific estate peers** (unique set), SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app integration, and real MCP tools.

## Peers (6)
`mem20simz` (counterfactual/compare/outcome_probability), `mem20eventstreamsuperhighwayz` (route events), `mem20capabilitymarketplacez` (route target capability), `mem20faultcontainmentcellsz` (failure/containment signal), `mem20universalhealthnervoussystemz` (health-aware routing), `mem20zerotouchnodeswarmz` (node targets/quorum). Failures reported, not fatal.

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

## Absorbed: `mem20eventstreamsuperhighwayz`

# RM-074 — Event Stream Superhighway

**Outcome:** Route high-volume typed events across local, edge, and cloud runtimes
**Breakthrough:** Every product can react to live data without custom plumbing
**Version:** 4.0.0 · **Subsystem:** `mem20eventstreamsuperhighwayz`

The superhighway is the transport layer of the mem20 estate. It routes typed
events, tracks per-subscriber offsets and lag, and — since 4.0 — it is wired
into the substrate rather than standing alone: every routed event can be
persisted to durable memory, searched multi-hop, announced to the fleet
gateway, verified for ledger integrity, screened for leaked credentials, and
compacted for the wire.

## Install

mem20 is **not on PyPI**. Install from source:

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -r requirements.txt
```

## Quick start — runnable example

This is the whole seam in one script: publish an event, persist it, announce it
to the fleet, read it back, and report on the stream. Run it from the repo root.

```bash
cd mem20
MEM20_STORE_PATH=/tmp/mem20-demo-store python3 - <<'PY'
import json, sys
sys.path.insert(0, "mem20eventstreamsuperhighwayz")

from mem20eventstreamsuperhighwayz import domain, integration

stream = domain.create_stream("orders")
domain.subscribe(stream, "billing")

out = integration.publish_and_persist(
    stream, "order.created", {"id": 7, "total": 42.5}, key="o-7"
)
print("event seq      :", out["event"]["seq"])
print("memory topic   :", out["memory_topic"])
print("announced by   :", out["announced"]["agent_name"])
print("screening clean:", out["screening"]["clean"])

rows = integration.recall_events("orders", "order.created")
print("recalled rows  :", len(rows))
print("recalled body  :", json.loads(rows[0]["content"])["payload"])

report = integration.stream_report(stream)
print("throughput/min :", report["throughput_per_min"])
print("lag            :", report["lag"])
print("inventory total:", report["inventory"]["total"])
PY
```

Real output from a run of the block above:

```
event seq      : 1
memory topic   : eventstream.orders.order.created
announced by   : eventstream-orders
screening clean: True
recalled rows  : 1
recalled body  : {'id': 7, 'total': 42.5}
throughput/min : 1.0
lag            : {'billing': 1}
inventory total: 312
```

## CLI

```bash
# publish + persist + announce
python3 -m mem20eventstreamsuperhighwayz publish \
    --stream orders --type order.created --payload '{"id": 7}' --key o-7

# operational report (stream + substrate in one object)
python3 -m mem20eventstreamsuperhighwayz report --stream orders --subscriber billing

# round-trip the memory engine and exit non-zero if the ledger is unfaithful
python3 -m mem20eventstreamsuperhighwayz verify

# measured estate inventory counts
python3 -m mem20eventstreamsuperhighwayz inventory

# multi-hop search over the event log
python3 -m mem20eventstreamsuperhighwayz search \
    "what is the p95 latency and which partition is hot"

# quantize a numeric payload for the wire
python3 -m mem20eventstreamsuperhighwayz compact 1.0 2.0 3.0 4.0 --bits 8
```

## MCP tools

Registered on the mem20 MCP server (`mcp/server.py` → `EventStreamToolsMixin`):

| Tool | What it does |
|---|---|
| `stream_publish` | Publish, persist and announce one event; returns the memory id |
| `stream_report` | Stream health + substrate health in one call |
| `stream_recall` | Read back persisted events for a stream/type |
| `stream_verify` | Round-trip the memory engine, report ledger fidelity |
| `stream_search` | Decompose a compound telemetry question into sub-retrievals |

## Estate wiring (criterion 6)

Every one of these is a real call on a tested path — see
`mem20eventstreamsuperhighwayz/tests/test_integration.py`.

| mem20 project | API used | Where |
|---|---|---|
| `memory_engine` | `memory.remember` / `memory.recall` / `memory.status` | `integration.remember_event`, `recall_events`, `memory_status` |
| `memory_engine` | `retrieval_v2.decompose_query` | `integration.search_events` |
| `toolchest` | `catalog.load_inventory` | `integration.capability_inventory` |
| `gateway` | `hermes_gateway.broadcast` / `register_agent` / `load_names` | `integration.announce` |
| `mem20verify` | `dataintegrity.check` | `integration.verify_memory_integrity` |
| `mem20ops` | `memchecks.identity_check` | `integration.identity_report` |
| `mem20corez` | `quantizer.quantize_tensor` | `integration.compact_payload` |
| `mem20secretz` | `sweep.classify` | `integration.screen_payload` |

### Three estate traps this subsystem has to handle

All three are real and all three are documented in `_bootstrap.py` rather than
papered over:

1. **Shim shadowing.** `mem20corez/__init__.py` is a version-only shim sitting
   next to the real package at `mem20corez/mem20corez/`. With the repo root on
   `sys.path`, `import mem20corez` resolves to the shim and `quantizer` is
   unreachable. `_bootstrap.ensure_estate_path()` puts the inner package parent
   ahead of the repo root and evicts an already-imported shim.
2. **`memory` shim vs engine.** The repo root ships a `memory.py` that
   re-exports `memory_engine.memory`. `mem20verify.dataintegrity.check()`
   rebinds `ENTRIES`/`LEDGER` on whatever `import memory` returns, so if the
   shim wins, the rebinding lands on the shim and the check reports 0
   round-trips while looking like a data-integrity failure.
   `verify_memory_integrity()` binds the real engine module first.
3. **`sweep` name collision.** `mem20secretz/__init__.py` re-exports the
   *function* `sweep`, which shadows the submodule of the same name on the
   package object — so `from mem20secretz import sweep` hands back a function
   with no `.classify`. The seam imports `from mem20secretz.sweep import
   classify` instead.

## Tests

```bash
python3 -m pytest mem20eventstreamsuperhighwayz -q
```

## Conformance

```bash
python3 scripts/renovation/conformance.py mem20eventstreamsuperhighwayz
```

## Public API

```python
from mem20eventstreamsuperhighwayz import domain, integration

# domain — the stream itself
domain.create_stream(name) -> dict
domain.publish(stream, event_type, payload, key=None) -> dict
domain.subscribe(stream, subscriber_id, filter_type=None) -> dict
domain.consume(stream, subscriber_id, batch=10) -> list[dict]
domain.throughput(stream, window_s=60) -> float
domain.lag(stream, subscriber_id) -> int

# integration — the seam onto the estate
integration.publish_and_persist(stream, event_type, payload, key=None, announce_to_fleet=True) -> dict
integration.remember_event(stream, event, actor="eventstream") -> dict
integration.recall_events(stream_name, event_type=None) -> list[dict]
integration.stream_report(stream, window_s=60) -> dict
integration.search_events(query, k=5) -> dict
integration.capability_inventory() -> dict
integration.announce(stream, event, agent_name=None) -> dict
integration.verify_memory_integrity() -> dict
integration.identity_report() -> dict
integration.compact_payload(values, bits=8) -> dict
integration.screen_payload(payload) -> dict
```

## Absorbed: `mem20faultcontainmentcellsz`

# mem20faultcontainmentcellsz — Fault Containment Cells

Circuit-breaker style fault containment (closed → open → half-open) with fail-fast behavior, plus mem20 estate integration.

## Python API

```python
import tempfile
from mem20faultcontainmentcellsz.domain import FaultContainmentCells, estate_context

cell = FaultContainmentCells(threshold=2, cool_down=10.0)
print(cell.call(lambda: 42))
print(cell.state)

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20faultcontainmentcellsz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20faultcontainmentcellsz/mem20faultcontainmentcellsz/tests -q
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

## Absorbed: `mem20devicecapabilitycompilerz`

# mem20devicecapabilitycompilerz — Device Capability Compiler

First-class mem20 subsystem for device capability detection and compilation targeting (detect, compile optimizations, feature flags, compatibility) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20crossplatformmicrokernelz`, `mem20datalocalityoptimizerz`, `mem20zerotouchnodeswarmz`, `mem20capabilitymarketplacez`, `mem20eventstreamsuperhighwayz`, `mem20universalhealthnervoussystemz`.

## Python API (runnable)
```python
from mem20devicecapabilitycompilerz.domain import detect_capabilities, compile_for_device, feature_flags, compatibility, compile_report, probe
c=detect_capabilities({"cpu_cores":4,"memory_gb":8}); print(c["tier"])  # high
print("ml_acceleration" in compile_for_device("x",c)["optimizations"])  # True
print(compatibility({"memory_gb":2},["memory_4gb"])["compatible"])  # False
r=compile_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20devicecapabilitycompilerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20devicecapabilitycompilerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20devicecapabilitycompilerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20devicecapabilitycompilerz serve --port 8801
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/devicecapabilitycompilerz/index.html` (no Vite edits).

## MCP & registration
`DeviceCapabilityCompilerToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20devicecapabilitycompilerz/mem20devicecapabilitycompilerz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20devicecapabilitycompilerz
```
Target **7/7**.

## Absorbed: `mem20energyawarecomputemigrationz`

# mem20energyawarecomputemigrationz — Energy-Aware Compute Migration (RM-047)

**Outcome:** schedule compute around battery, thermal limits, electricity price, and renewable availability.  
**Breakthrough:** the fleet optimizes both performance and energy use.

A real, first-class migration control plane: legacy-compatible domain primitives (preserved for `mem20causalroutingbrainz`), advanced energy/carbon/battery/thermal/renewable scoring and migration planning, SQLite WAL state, service/CLI/JSON HTTP API, served cockpit, `docs/app` monitor, and six **unique** cross-subsystem peers (different set from #300, #301, #302).

## Legacy-compatible API (preserved)
`energy_cost(node, workload_size)`, `migrate_decision(src, dst, workload)`, `carbon_footprint(node, workload_size)`, `greenest_node(nodes, workload)` (deterministic tie-break by node id), `migration_plan(workloads, nodes)`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls used | Contribution |
|---|---|---|
| `mem20batteryawareagentschedulerz` | `BatteryAwareAgentScheduler.schedule/cheapest_slot` | power-budget/battery feasibility and cheapest slot |
| `mem20energyawarefoundationz` | `power_reading`, `threshold_check`, `energy_budget`, `optimize_power`, `daily_energy` | energy thresholds/budget/optimization |
| `mem20datalocalityoptimizerz` | `placement_score`, `optimal_placement`, `migration_cost`, `locality_report` | data locality and migration/egress cost |
| `mem20causalroutingbrainz` | `DemandForecastAndCapacityBrain.observe/forecast/residual_sigma/capacity_for` | capacity forecast with uncertainty |
| `mem20goaleconomyschedulerz` | `schedule_goals`, `goal_value`, `priority_queue`, `progress` | migration prioritization by value/cost |
| `mem20planetarybatchfabricz` | `submit_job`, `schedule`, `fabric_health`, `retry` | batch/workload placement and fabric health |

## CLI
```bash
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 status
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 doctor
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 simulate
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 node add --id green --power 50 --speed 2 --rate 0.10 --carbon 100 --renewable 80
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 node add --id dirty --power 200 --speed 1 --rate 0.20 --carbon 600 --renewable 0
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 workload add --id job-1 --size 10 --current-node dirty
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 plan
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 migrate --workload job-1 --to green
python -m mem20energyawarecomputemigrationz --db state/eam.sqlite3 serve --port 8783
```

## Runnable example (verified)
```bash
cd /opt/mem20
DB=/tmp/eam-demo.sqlite3
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20energyawarecomputemigrationz --db "$DB" node add --id green --power 50 --speed 2 --rate 0.10 --carbon 100 --renewable 80 >/dev/null
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20energyawarecomputemigrationz --db "$DB" node add --id dirty --power 200 --speed 1 --rate 0.20 --carbon 600 --renewable 0 >/dev/null
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20energyawarecomputemigrationz --db "$DB" workload add --id job-1 --size 10 --current-node dirty >/dev/null
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20energyawarecomputemigrationz --db "$DB" plan
```

Observed (real run, key fields):
```text
ok=true
plan.counts: workloads=1 migrations=1 (dirty -> green when savings/feasibility justify)
signals: capacity_forecast, goal_scheduler, data_locality, batch_fabric all ok
placement: target chosen by energy+carbon+battery/thermal/renewable feasibility scoring
```

`migrate` applies the move in durable state and returns energy/locality signals. `doctor` probes all 6 peers; `simulate` runs real scenarios.

## HTTP API / web
`GET /api/status|doctor|nodes|workloads|events|migrations`, `POST /api/nodes|workloads|plan|migrate|snapshot|restore|simulate|benchmark`, cockpit at `/`. Docs monitor: `docs/app/energy-migration/index.html` (`?api=`).

## Tests
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20energyawarecomputemigrationz/tests -q
```
Covers legacy domain compatibility (including tie-break), 6 ecosystem peers (real calls), service plan/migrate/status/doctor/simulate, and HTTP/cockpit.

## Conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20energyawarecomputemigrationz
```
Target 7/7.

## Limits
No claim of production grid/carbon market feeds, real device power telemetry, live data replication, or managed workload migration agents. Decisions are modeled over declared node/workload state; actual execution hooks are integration points.

## Absorbed: `mem20realworldimpactrewardsz`

# mem20realworldimpactrewardsz — Real-World Impact Rewards

First-class mem20 subsystem for real-world impact rewards (record impact, compute rewards, leaderboards) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20dynamicquestrewardcomposerz`, `mem20crossproductloyaltygraphz`, `mem20customerlifecycleenginez`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## Python API (runnable)
```python
from mem20realworldimpactrewardsz.domain import record_impact, compute_reward, leaderboard, impact_report, probe
i={}; record_impact(i,"alice","cleanup",2.0); print(compute_reward(i,"alice"))  # 2.0
print(leaderboard(i)[0]["user"])  # alice
r=impact_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realworldimpactrewardsz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realworldimpactrewardsz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realworldimpactrewardsz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realworldimpactrewardsz serve --port 8814
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/realworldimpactrewardsz/index.html` (no Vite edits).

## MCP & registration
`RealWorldImpactRewardsToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20realworldimpactrewardsz/mem20realworldimpactrewardsz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20realworldimpactrewardsz
```
Target **7/7**.

## Absorbed: `mem20roamingworkloadschedulerz`

# mem20roamingworkloadschedulerz — Roaming Workload Scheduler

First-class mem20 subsystem for roaming workload scheduling (schedule, migrate, node load, health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20zerotouchnodeswarmz`, `mem20autonomousworkcellsz`, `mem20causalroutingbrainz`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20roamingworkloadschedulerz.domain import schedule, migrate, scheduler_report, probe
nodes=[{"id":"a","load":0},{"id":"b","load":5}]; print(schedule([{"id":"w","cost":1}],nodes)[0]["node"])  # a
print(migrate("w","a","b")["to"])  # b
r=scheduler_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20roamingworkloadschedulerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20roamingworkloadschedulerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20roamingworkloadschedulerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20roamingworkloadschedulerz serve --port 8820
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/roamingworkloadschedulerz/index.html` (no Vite edits).

## MCP & registration
`RoamingWorkloadSchedulerToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20roamingworkloadschedulerz/mem20roamingworkloadschedulerz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20roamingworkloadschedulerz
```
Target **7/7**.

## Absorbed: `mem20selfhealingplansz`

# mem20selfhealingplansz — Self-Healing Plans

First-class mem20 subsystem for self-healing plans (create/execute with auto-retry, status, heal/reset) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20faultcontainmentcellsz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20universalhealthnervoussystemz`, `mem20causalroutingbrainz`, `mem20autonomousrecoverydirectorz`.

## Python API (runnable)
```python
from mem20selfhealingplansz.domain import create_plan, execute_step, plan_status, heal_plan, healing_report, probe
p=create_plan(["a"]); execute_step(p,0,lambda n: None); print(plan_status(p)["done"])  # 1
r=healing_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfhealingplansz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfhealingplansz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfhealingplansz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfhealingplansz serve --port 8825
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/selfhealingplansz/index.html` (no Vite edits).

## MCP & registration
`SelfHealingPlansToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20selfhealingplansz/mem20selfhealingplansz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20selfhealingplansz
```
Target **7/7**.

## Absorbed: `mem20skillmemorytransferz`

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

## Absorbed: `mem20webhooksupernetworkz`

# RM-078 — Webhook Supernetwork

Outcome: receive, verify, deduplicate, route, replay, and transform events from
any provider.

Breakthrough: webhook chaos becomes a dependable programmable event layer.

## What this package actually guarantees

| Guarantee | How |
|---|---|
| A forged delivery is refused | HMAC-SHA256 over `timestamp.body`, compared with `hmac.compare_digest` |
| A captured delivery cannot be replayed later | the timestamp is *inside* the signed material, and a tolerance window rejects anything stale |
| A redelivery does not double-process | a stable idempotency key per delivery, deduplicated through a bounded, optionally durable ledger |
| A replay cannot quietly re-deliver a subset | `mem20verify.dataintegrity.check` must prove the store round-trips a write first |
| A credential never enters the event log | `mem20secretz.sweep.classify` classifies field names *and* values, and the payload is refused rather than stored |
| A route cannot exist for a prohibited use | `mem20liez.gates.check_prohibited_uses` is consulted at construction |
| The sender's clock cannot poison the event time | `memory_engine.memory.validate_event_time` decides what a legal event time is |

Two defects fixed on this branch, both of which made the guarantees above hollow:

* the dedupe ledger was an unbounded in-memory `list`, so **every process
  restart forgot what it had delivered** and re-delivered everything. It is now
  a `DeliveryLedger` with a cap and an optional append-log.
* payloads were eligible to be persisted verbatim. A webhook log is durable and
  replayed, so persisting a payload containing a token turned the log into a
  credential archive that got re-read on every replay. `admit()` now refuses it.

## Quickstart

The block below is the real CLI, and it is the exact command used to verify this
package. It needs no secret and touches nothing outside a temporary directory:

```bash
python3 -m mem20webhooksupernetworkz.cli selftest
```

Expected (10 checks, all true):

```json
{
  "checks": 10,
  "failed": [],
  "ok": true,
  "passed": 10
}
```

## Wiring, end to end

```bash
# 1. Confirm every sibling project this receiver depends on is reachable.
python3 -m mem20webhooksupernetworkz.cli doctor --secret "$MEM20_WEBHOOK_SECRET"

# 2. Sign a body the way a provider would, for a timestamp inside the window.
python3 -m mem20webhooksupernetworkz.cli sign '{"deploy":"staging"}' \
    --timestamp 1772323200 --secret "$MEM20_WEBHOOK_SECRET"

# 3. Verify a delivery. Add --payload to also check the credential class.
python3 -m mem20webhooksupernetworkz.cli verify '{"deploy":"staging"}' \
    --timestamp 1772323200 --signature "$SIG" \
    --secret "$MEM20_WEBHOOK_SECRET" --now 1772323200

# 4. Deliver once per idempotency key - a repeat is skipped, not re-sent.
python3 -m mem20webhooksupernetworkz.cli deliver '{"deploy":"staging"}' \
    --timestamp 1772323200 --signature "$SIG" --idem deploy-1 \
    --secret "$MEM20_WEBHOOK_SECRET" --now 1772323200

# 5. Replay a stored event log - refuses if the store cannot round-trip.
python3 -m mem20webhooksupernetworkz.cli replay events.jsonl \
    --secret "$MEM20_WEBHOOK_SECRET"
```

Exit codes: `0` accepted, `2` verification refused, `3` payload refused,
`4` replay refused because the store failed verification.

## Estate dependencies

This package is wired into six sibling projects; each call answers a question
this receiver cannot answer alone.

| Project | Symbol | Question |
|---|---|---|
| `mem20secretz` | `sweep.classify` | may this payload be persisted |
| `mem20liez` | `gates.check_prohibited_uses` | may this route exist |
| `mem20verify` | `dataintegrity.check` | can the store be replayed from |
| `mem20ops` | `memchecks.identity_check` | which store is this |
| `memory_engine` | `memory.validate_event_time` | is the sender's time legal |
| `toolchest` | `catalog.load_inventory` | what may a route target |

`mem20` installs from source, not PyPI. Run from a checkout root so the seam can
find the sibling projects; `doctor` names any that are missing instead of
failing with one traceback.

## Note on the engine module

`memory_engine/memory.py` is imported by the estate under two names
(`memory_engine.memory` and `memory`). Python caches those as **two independent
modules**, so `STORE_DIR`/`LEDGER` and the vector/BM25 indexes exist twice for a
single store. The visible symptom is a false integrity failure — `mem20verify`
writes through one copy and reports "no ledger row written" about a healthy
store, which blocks every replay.

`estate.py` aliases the two names to one module object on import, and
`estate.resync_engine_store()` re-points and re-aliases after a store change.
`tests/test_estate_wiring.py::TestSingleEngineInstance` pins both.

## Tests

```bash
python3 -m pytest mem20webhooksupernetworkz -q
```

## Absorbed: `mem20zerotouchnodeswarmz`

# mem20zerotouchnodeswarmz — Zero-Touch Node Swarm

First-class mem20 subsystem for zero-touch node swarming (register_node/discover/node_score/assign_task/mark_failed/heal/quorum/load_distribution/join_token) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20roamingworkloadschedulerz`, `mem20causalroutingbrainz`, `mem20capabilitymarketplacez`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20autonomousrecoverydirectorz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20zerotouchnodeswarmz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20zerotouchnodeswarmz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20zerotouchnodeswarmz serve --port 8846
```
