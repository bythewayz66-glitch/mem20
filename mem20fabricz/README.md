# mem20fabricz — crew runtime

mem20 integration fabric runtime.

## Members (23)

Reviewed packages grouped here for joint integration under the
package-review rulings:

- `mem20apishapeshiftinggatewayz`
- `mem20rewardforgez`
- `mem20collectivemodelintelligencez`
- `mem20rewardforgez`
- `mem20crisisresponsemeshz`
- `mem20crossruntimeeventlatticez`
- `mem20edgetransportfabricz`
- `mem20eventstreamsuperhighwayz`
- `mem20federatedmodellearningmeshz`
- `mem20freestackambientcomputingfabricz`
- `mem20livemodelfusionz`
- `mem20modalitybridgez`
- `mem20modelsleepandwakesystemz`
- `mem20nearbydevicemeshz`
- `mem20offlineresiliencemeshz`
- `mem20personalmodelevolutionz`
- `mem20planetarybatchfabricz`
- `mem20rewardforgez`
- `mem20sensorfusiongatewayz`
- `mem20rewardforgez`
- `mem20rewardforgez`
- `mem20temporaldatabasefabricz`
- `mem20universalintegrationcompilerz`

## Status

Skeleton slice: registry, CLI (`--version`, `--members`), hermetic
tests. Member wiring arrives in the integration phase.

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20fabricz --version
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20fabricz --members
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20fabricz status
```

## Absorbed: `mem20apishapeshiftinggatewayz`

# mem20apishapeshiftinggatewayz — API Shape-Shifting Gateway

Adapt payloads, route versions, diff schemas, and transform responses, with mem20 estate integration and governance wiring.

## Python API

```python
import tempfile
from mem20apishapeshiftinggatewayz.domain import transform_payload, version_route, schema_diff, adapt_response, estate_context

print(transform_payload({"old_name": 1}, {"old_name": "new_name"}))
print(version_route("/items", 2))
print(schema_diff({"properties": {"a": {}}}, {"properties": {"a": {}, "b": {}}}))
print(adapt_response({"ok": True}, target_version=3))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20apishapeshiftinggatewayz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20apishapeshiftinggatewayz/mem20apishapeshiftinggatewayz/tests mem20apishapeshiftinggatewayz/tests -q
```

## Absorbed: `mem20collectivemodelintelligencez`

# mem20collectivemodelintelligencez — Collective Model Intelligence

First-class mem20 subsystem for collective model intelligence: weighted ensemble prediction, voting, diversity measurement, knowledge distillation loss, and confidence aggregation — with **6 collective-model-specific peers** (unique set), SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app integration, and real MCP tools.

## Peers (6)
`mem20livemodelfusionz` (fuse/weight/select/best/vote), `mem20loreragcontentgeneratorz` (generation quality), `mem20capabilitymarketplacez` (model routing), `mem20eventstreamsuperhighwayz` (ensemble events), `mem20universalhealthnervoussystemz` (model health), `mem20causalroutingbrainz` (causal route scoring). Failures reported, not fatal.

## Python API (runnable)
```python
from mem20collectivemodelintelligencez.domain import ensemble_predict, diversity_score, knowledge_distill, aggregate_confidence, collective_report, probe, estate_context
print(ensemble_predict([1,2,3]))           # 2.0
print(ensemble_predict(["a","a","b"]))     # a
print(diversity_score([1,1,2]))            # 0.3333
print(knowledge_distill([1,0],[0.9,0.1]))  # ~0.01
print(aggregate_confidence([0.8,0.6]))     # 0.7
r = collective_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"], estate_context()["peer_count"])      # True 6
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20collectivemodelintelligencez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20collectivemodelintelligencez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20collectivemodelintelligencez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20collectivemodelintelligencez simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20collectivemodelintelligencez serve --port 8790
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit at `/`. State `~/.mem20/collectivemodelintelligencez/state.sqlite3` (WAL). docs/app: `docs/app/collectivemodelintelligencez/index.html` (no Vite edits).

## MCP & registration
`CollectiveModelIntelligenceToolsMixin` in `mcp/server.py`. Gateway `SUBSYSTEMS` entry.

## Tests & conformance
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20collectivemodelintelligencez/mem20collectivemodelintelligencez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20collectivemodelintelligencez
```
Target **7/7**.

## Absorbed: `mem20crossruntimeeventlatticez`

# RM-005 — Cross-Runtime Event Lattice

**Outcome:** Connect independent runtimes through typed events, durable streams, and reactive subscriptions
**Breakthrough:** The ecosystem behaves like one nervous system without becoming monolithic
**Version:** 4.0.0 · **Subsystem:** `mem20crossruntimeeventlatticez`

The lattice is the causality layer of the mem20 estate. It emits typed events,
orders them, links them into a vector-clock DAG, and merges independent
lattices into one. Since 4.0 it is wired into the substrate rather than
standing alone: every lattice event can be persisted to durable memory,
searched multi-hop, announced to the fleet gateway, verified for ledger
integrity, and compacted for the wire.

## Install

mem20 is **not on PyPI**. Install from source:

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -r requirements.txt
```

## Quick start — runnable example

This is the whole seam in one script: emit an event, link a child to it
causally, persist both, announce them to the fleet, read them back, and report
on the merged lattice. Run it from the repo root.

```bash
cd mem20
MEM20_STORE_PATH=/tmp/mem20-lattice-demo python3 - <<'PY'
import json, sys
sys.path.insert(0, "mem20crossruntimeeventlatticez")

from mem20crossruntimeeventlatticez import domain, integration

parent = domain.emit("session.start", {"user": "u-1"}, source="local")
out = integration.emit_and_record(
    "session.view", {"page": "/pricing"}, lattice="web", source="edge", parent=parent
)
print("event id       :", out["event"]["id"])
print("parent         :", out["event"]["parent"])
print("vector clock   :", out["event"]["vector"])
print("memory topic   :", out["memory_topic"])
print("announced by   :", out["announced"]["agent_name"])

rows = integration.recall_events("web", "session.view")
print("recalled rows  :", len(rows))
print("recalled body  :", json.loads(rows[0]["content"])["payload"])

report = integration.lattice_report(
    [{"events": [parent]}, {"events": [out["event"]]}], name="web"
)
print("lattice count  :", report["count"])
print("by type        :", report["by_type"])
print("sources        :", report["sources"])
print("causal links   :", report["causal_links"])
print("inventory total:", report["inventory"]["total"])
PY
```

Real output from a run of the block above:

```
Agent registered: lattice-web
  Location: mem20crossruntimeeventlatticez
  Agent ID: 6c39be61
  Registered: 2026-11-01T19:24:29.888889+00:00
Broadcast from lattice-web: session.view id=0544c243 source=edge...
event id       : 0544c243
parent         : 5ac56c4c
vector clock   : {'5ac56c4c': 1793561069.8869495}
memory topic   : lattice.web.session.view
announced by   : lattice-web
recalled rows  : 1
recalled body  : {'page': '/pricing'}
lattice count  : 2
by type        : {'session.start': 1, 'session.view': 1}
sources        : ['edge', 'local']
causal links   : 1
inventory total: 312
```

## CLI

```bash
# emit + link + persist + announce
python3 -m mem20crossruntimeeventlatticez emit \
    --type click --payload '{"x": 1}' --lattice web --source edge

# operational report for a merged lattice
python3 -m mem20crossruntimeeventlatticez report --lattice web --lattices 2 --events 2

# round-trip the memory engine and exit non-zero if the ledger is unfaithful
python3 -m mem20crossruntimeeventlatticez verify

# measured estate inventory counts
python3 -m mem20crossruntimeeventlatticez inventory

# multi-hop search over lattice history
python3 -m mem20crossruntimeeventlatticez search \
    "which runtime emitted the first failure and what did it cause"

# quantize a numeric payload for the wire
python3 -m mem20crossruntimeeventlatticez compact 1.0 2.0 3.0 4.0 --bits 8
```

## MCP tools

Registered on the mem20 MCP server (`mcp/server.py` → `LatticeToolsMixin`):

| Tool | What it does |
|---|---|
| `lattice_emit` | Emit, causally link, persist and announce one event |
| `lattice_report` | Merged-lattice health + substrate health in one call |
| `lattice_recall` | Read back persisted events for a lattice/type |
| `lattice_verify` | Round-trip the memory engine, report ledger fidelity |
| `lattice_search` | Decompose a compound causality question into sub-retrievals |

## Estate wiring (criterion 6)

Every one of these is a real call on a tested path — see
`mem20crossruntimeeventlatticez/tests/test_integration.py`.

| mem20 project | API used | Where |
|---|---|---|
| `memory_engine` | `memory.remember` / `memory.recall` / `memory.status` | `integration.remember_event`, `recall_events`, `memory_status` |
| `memory_engine` | `retrieval_v2.decompose_query` | `integration.search_history` |
| `toolchest` | `catalog.load_inventory` | `integration.capability_inventory` |
| `gateway` | `hermes_gateway.broadcast` / `register_agent` / `load_names` | `integration.announce` |
| `mem20verify` | `dataintegrity.check` | `integration.verify_memory_integrity` |
| `mem20ops` | `memchecks.identity_check` | `integration.identity_report` |
| `mem20corez` | `quantizer.quantize_tensor` | `integration.compact_payload` |

### Two estate traps this subsystem has to handle

Both are real and both are documented in `_bootstrap.py` rather than papered
over:

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

## Tests

```bash
python3 -m pytest mem20crossruntimeeventlatticez -q
```

## Conformance

```bash
python3 scripts/renovation/conformance.py mem20crossruntimeeventlatticez
```

## Public API

```python
from mem20crossruntimeeventlatticez import domain, integration

# domain — the lattice itself
domain.emit(event_type, payload, source="local") -> dict
domain.order_events(events) -> list[dict]
domain.causal_link(parent, child) -> dict
domain.lattice_merge(lattices) -> dict
domain.filter_by_type(events, etype) -> list[dict]

# integration — the seam onto the estate
integration.emit_and_record(event_type, payload, lattice="default", source="local", parent=None, announce_to_fleet=True) -> dict
integration.remember_event(event, lattice="default", actor="lattice") -> dict
integration.recall_events(lattice, event_type=None) -> list[dict]
integration.lattice_report(lattices, name="default", window_s=60) -> dict
integration.search_history(query, k=5) -> dict
integration.capability_inventory() -> dict
integration.announce(event, lattice="default", agent_name=None) -> dict
integration.verify_memory_integrity() -> dict
integration.identity_report() -> dict
integration.compact_payload(values, bits=8) -> dict
```

## Absorbed: `mem20edgetransportfabricz`

# mem20edgetransportfabricz — Edge Transport Fabric (RM-077)

**Outcome:** move bounded data and commands across intermittently connected nodes.  
**Breakthrough:** devices and remote sites remain integrated even with poor connectivity.

This subsystem is a real, first-class transport control plane: typed domain logic (legacy-compatible primitives + advanced fabric model), a durable SQLite WAL state plane, a service that owns topology/admission/routing/reservations/reroute, cross-subsystem judgements from six **unique** peers (a different set from `mem20causalroutingbrainz` #300 and `mem20edgetocloudintelligencecontinuumz` #301), a CLI, a JSON HTTP API, a served operator cockpit, and a `docs/app` monitor.

## What it does

- **Legacy-compatible transport primitives:** `route_path(src,dst,nodes)` (neighbor map), `qos_class(latency_ms,priority)`, `allocate_bandwidth(total,demands)`, `transport_health(links)` — preserved for existing callers (including `mem20edgetocloudintelligencecontinuumz`).
- **Fabric routing:** bandwidth-aware shortest path over node/link topology with link status (up/degraded/intermittent/down), latency/jitter/loss/cost/reservation weights, QoS/SLA checks, and alternative paths.
- **Intermittent connectivity:** when strict constraints cannot be met but intermittent delivery is acceptable, the fabric returns an explicit degraded/bounded plan instead of hiding failure.
- **Admission & capacity:** token-bucket/traffic admission signals, bandwidth reservation/release, congestion/utilization/health.
- **Resilience:** fault containment/circuit-breaker signals, self-healing retry semantics, causal route influence, recovery planning, and explicit reroute plans.
- **Observability:** append-only events, placement journal, telemetry stream publication, snapshots/restore, status/doctor/simulate/benchmark.

## Architecture

| Layer | File | Responsibility |
|---|---|---|
| Domain | `mem20edgetransportfabricz/domain.py` | Legacy-compatible functions + `FabricNode`/`FabricLink`/`FlowDemand`/`PathDecision`, bandwidth-aware routing, QoS/SLA, admission, reservation, reroute, fabric/transport health. Pure (no I/O). |
| State plane | `mem20edgetransportfabricz/store.py` | SQLite WAL: versioned nodes/links/flows, events, placements, idempotency, snapshots/restore. |
| Ecosystem | `mem20edgetransportfabricz/ecosystem.py` | Six unique peer adapters with real calls and fail-open reporting. |
| Service | `mem20edgetransportfabricz/service.py` | Topology CRUD, admit/route/reserve/release/reroute, status/doctor/events/placements/snapshots, simulate/benchmark; peer signals on real operations. |
| Runtime | `mem20edgetransportfabricz/runtime.py` | CLI + `ThreadingHTTPServer` JSON API + static cockpit (`web/`), CORS, error mapping (400/404/409). |
| Web | `mem20edgetransportfabricz/web/` | Operator cockpit. |

## Unique cross-subsystem wiring (criterion 6)

**Rule:** the ≥5 cross-module peers must be a **different set on each subsystem**. This fabric uses a transport-specific set, different from #300 and #301:

| Peer | Real calls used | What it contributes |
|---|---|---|
| `mem20meshz.mem20meshz.meshes.selfhealing.domain` | `SelfHealingConnectorMesh.call/delay_for` | Resilient transient delivery/retry with backoff/jitter |
| `mem20autonomoustrafficcontrollerz.domain` | `TokenBucket.allow/retry_after`, `LeakyBucket` | Admission control/backpressure for link/flow demand |
| `mem20faultcontainmentcellsz.domain` | `FaultContainmentCells.call/state` | Circuit breaking/fail-fast containment |
| `mem20causalroutingbrainz.domain` | `route_by_cause`, `causal_effect`, `confounder_adjust`, `intervention_value` | Causal/weighted route influence |
| `mem20autonomousrecoverydirectorz.domain` | `triage`, `rollback_plan`, `remediate`, `recovery_time`, `health_after` | Incident recovery/remediation planning |
| `mem20eventstreamsuperhighwayz.domain` | `create_stream/publish/subscribe/consume/throughput/lag` | Fabric telemetry/flow event stream |

All are invoked on normal paths (node/link upsert, admit/route/reserve/reroute/status/doctor/simulate) and exercised by the subsystem’s tests.

## CLI

```bash
python -m mem20edgetransportfabricz --db state/transport.sqlite3 status
python -m mem20edgetransportfabricz --db state/transport.sqlite3 doctor
python -m mem20edgetransportfabricz --db state/transport.sqlite3 simulate
python -m mem20edgetransportfabricz --db state/transport.sqlite3 benchmark --iterations 20
python -m mem20edgetransportfabricz --db state/transport.sqlite3 node add --id edge-a --capacity 1000
python -m mem20edgetransportfabricz --db state/transport.sqlite3 node add --id edge-b --capacity 1000
python -m mem20edgetransportfabricz --db state/transport.sqlite3 link add --src edge-a --dst edge-b --bandwidth 100 --latency 10 --status up
python -m mem20edgetransportfabricz --db state/transport.sqlite3 flow admit --id flow-1 --src edge-a --dst edge-b --demand 5 --priority 2 --max-latency 100
python -m mem20edgetransportfabricz --db state/transport.sqlite3 flow route --src edge-a --dst edge-b --demand 5
python -m mem20edgetransportfabricz --db state/transport.sqlite3 flow reroute flow-1 --avoid edge-a->edge-b --reason failure
python -m mem20edgetransportfabricz --db state/transport.sqlite3 events --limit 20
python -m mem20edgetransportfabricz --db state/transport.sqlite3 serve --host 127.0.0.1 --port 8782
```

## Runnable example (verified)

```bash
cd /opt/mem20
DB=/tmp/etf-demo.sqlite3
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20edgetransportfabricz --db "$DB" node add --id edge-a --capacity 1000 >/dev/null
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20edgetransportfabricz --db "$DB" node add --id edge-b --capacity 1000 >/dev/null
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20edgetransportfabricz --db "$DB" link add --src edge-a --dst edge-b --bandwidth 100 --latency 10 --status up >/dev/null
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20edgetransportfabricz --db "$DB" flow admit --id flow-1 --src edge-a --dst edge-b --demand 5 --priority 2 --max-latency 100
```

Observed (real run, key fields):

```text
ok=true
decision: admitted=true path=['edge-a','edge-b'] latency_ms=10.0 bottleneck_mbps=100.0 qos=premium
signals: causal/traffic/containment/mesh/telemetry all ok
sla: ok=true (bandwidth, path_exists)
```

`admit` computes a bandwidth-aware path, checks QoS/SLA, records the durable flow/placement, and returns peer signals (causal route, traffic admission, fault containment, mesh resilience, telemetry). Poor/intermittent links return explicit degraded plans/reasons rather than hidden failure.

## HTTP API

The server (`serve`) hosts JSON API and the static cockpit at `/`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/status` | fabric/legacy health, metrics, telemetry signal |
| GET | `/api/nodes`, `/api/links`, `/api/flows`, `/api/flows/{id}` | topology/flows |
| POST | `/api/nodes`, `/api/links` | upsert node/link (peer signals returned) |
| POST | `/api/links/{id}/status` | set link status (recovery/containment/telemetry) |
| POST | `/api/flows/admit`, `/api/route` | admit flow / route query |
| POST | `/api/reserve`, `/api/release`, `/api/reroute` | capacity and reroute operations |
| GET | `/api/events?since=&limit=`, `/api/placements?flow_id=` | event/placement journals |
| GET | `/api/doctor`, `/api/metrics` | peer probe and store metrics |
| POST | `/api/snapshot`, `/api/restore`, `/api/simulate`, `/api/benchmark` | state/scenarios |
| GET | `/`, `/app.js`, `/style.css` | operator cockpit |

Errors are JSON with real status codes (400 validation, 404 missing, 409 conflict).

## Web surfaces

- **Per-subsystem cockpit:** served from the fabric process at `GET /` (`web/index.html`, `app.js`, `style.css`).
- **docs/app integration:** `docs/app/transport/index.html` — static estate monitor connecting to the fabric API (`?api=`/stored base URL). Linked from `docs/app/README.md`. (Compiled Vite assets are not modified.)

## State, safety, and resilience

- SQLite WAL state plane with version checks/conflict errors, append-only events/placements, idempotent admission, snapshots/restore.
- Admission is bandwidth/latency/SLA aware; infeasible or degraded paths include explicit reasons.
- Reroute avoids failed links and reports recovery/containment/mesh/telemetry signals.
- Cross-subsystem failures are reported as `ok:false` signals; they do not fabricate transport success.

## Tests

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20edgetransportfabricz/tests -q
```

Covers legacy domain compatibility, advanced routing/QoS/SLA/reservation/reroute/intermittent behavior, all six ecosystem adapters (real calls), service lifecycle/admission/reroute/status/doctor/simulate, runtime/CLI parser, and HTTP API + static cockpit.

## Conformance

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20edgetransportfabricz
```

Target: 7/7 — real domain logic (no stubs), tests, CLI, runnable README example, ≥5 cross-modules imported and called on covered lines, gateway/MCP registration.

## Limits (honest)

- No claim of production mesh radios, provider SD-WAN controllers, real NIC/driver/device integration, or managed global control plane credentials.
- Peer signals are real computations from the current subsystems; they do not replace network operator control planes or field radios.
- Bounded data/command movement is modeled as routing, admission, reservation, QoS/SLA, and state decisions; actual packet replication, store-and-forward queues, and application-level delivery guarantees are integration responsibilities.

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

## Absorbed: `mem20freestackambientcomputingfabricz`

# mem20freestackambientcomputingfabricz — FreeStack Ambient Computing Fabric (RM-211, #314)

**Outcome:** make FreeStack available as a continuous intelligence layer across desktop, mobile, home, vehicle, headset, and edge devices.  
**Breakthrough:** the platform follows the user and composes the right interface everywhere.

Preserves legacy domain API (#304 peer dependency) and CAPABILITY Engine/CLI/10-scenario simulator; enriches analyze/execute with ambient fabric analysis and 6 **unique** peer integrations (different from #300–#313).

## Legacy domain API (preserved)
`pool_resources(nodes)`, `discover_services(fabric,capability)`, `allocate(fabric,request)`, `fabric_health(fabric)`, `ambient_score(fabric)`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls | Contribution |
|---|---|---|
| `mem20fabricz` | `dispatch_plan`,`probe_members` | integration fabric dispatch/planning |
| `mem20hardwareawareinferencecompilerz` | `fuse_ops`,`quantize`,`schedule`,`memory_estimate` | hardware-aware inference/resource compilation |
| `mem20capabilitymarketplacez` | `CapabilityMarketplace` (+ method call) | capability discovery |
| `mem20crossplatformmicrokernelz` | `create_process`,`allocate_memory`,`schedule` | ambient workload process/memory/scheduling |
| `mem20secretslessworkloadidentityz` | `issue_identity`,`verify`,`rotate`,`identity_health` | secretsless workload identity |
| `mem20ambientdevicecompanionz` | `sense_context`,`proactive_suggestion` | ambient device context/suggestions |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20freestackambientcomputingfabricz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20freestackambientcomputingfabricz execute '{"nodes":[{"cpu":4,"memory":8,"status":"online"}],"capability":"compute","request":{"cpu":1,"memory":1},"values":[1,2,3]}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20freestackambientcomputingfabricz serve --port 8794
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20freestackambientcomputingfabricz/tests mem20freestackambientcomputingfabricz/mem20freestackambientcomputingfabricz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20freestackambientcomputingfabricz
```

## Absorbed: `mem20livemodelfusionz`

# mem20livemodelfusionz — Live Model Fusion

Combine specialist model outputs dynamically (weighted fusion, confidence weighting, best-model selection, ensemble voting) with mem20 estate integration.

## Python API

```python
import tempfile
from mem20livemodelfusionz.domain import fuse, ensemble_vote, estate_context

models = [{"outputs": {"score": 1.0}, "confidence": 0.8}, {"outputs": {"score": 3.0}, "confidence": 0.2}]
print(fuse(models)["fused"])
print(ensemble_vote(["a", "b", "a"]))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20livemodelfusionz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20livemodelfusionz/mem20livemodelfusionz/tests -q
```

## Absorbed: `mem20modalitybridgez`

# RM-064 — Modality Bridge

Outcome: Translate tasks and representations across text, image, audio, video, 3D, and sensor models

Breakthrough: Any model can cooperate with modalities it was not originally designed to handle

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `analyze` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20modalitybridgez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20modalitybridgez benchmark
```

## Absorbed: `mem20modelsleepandwakesystemz`

# RM-066 — Model Sleep and Wake System (#336)

**Outcome:** Hibernate rarely used models and restore them predictively before demand arrives.  
**Operation kind:** `forecast`.

## 1st-class implementation
- **Domain:** `track_activity/should_sleep/sleep/wake/sleep_health` (legacy) plus `plan_hibernation`, `predictive_wake_schedule`, `sleepwake_report`.
- **Runtime:** `forecast` wired to sleep/wake report + 6 peer signals (+ forecast series).
- **Ecosystem (6 peers, unique set):** `mem20causalroutingbrainz`, `mem20batteryawareagentschedulerz`, `mem20roamingworkloadschedulerz`, `mem20selftuningresourcegovernorz`, `mem20energyawarecomputemigrationz`, `mem20runtimecompatibilityenginez`.

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20modelsleepandwakesystemz execute '{"models":[{"id":"m1","state":"awake","last_activity":0}],"idle_threshold":1,"series":[1,2,3]}'
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20modelsleepandwakesystemz/mem20modelsleepandwakesystemz/tests/test_domain.py -q
```
Gateway `SUBSYSTEMS["mem20modelsleepandwakesystemz"]`; docs `docs/app/modelsleepandwakesystemz/index.html`; target 7/7.

## Absorbed: `mem20personalmodelevolutionz`

# mem20personalmodelevolutionz — Personal Model Evolution

First-class mem20 subsystem for personal model evolution (create_model/adapt/predict/reset/evolution_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20collectivemodelintelligencez`, `mem20skillmemorytransferz`, `mem20episodicmemorygraphz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20personalmodelevolutionz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20personalmodelevolutionz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20personalmodelevolutionz serve --port 8853
```

## Absorbed: `mem20planetarybatchfabricz`

# mem20planetarybatchfabricz — Planetary Batch Fabric

First-class mem20 subsystem for planetary batch fabric (submit_job/schedule/job_status/fabric_health/retry) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20roamingworkloadschedulerz`, `mem20autonomousworkcellsz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20autonomousrecoverydirectorz`, `mem20agentoutputcompilerz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20planetarybatchfabricz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20planetarybatchfabricz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20planetarybatchfabricz serve --port 8856
```

## Absorbed: `mem20rewardforgez`

# mem20rewardforgez — Reward Forge (unified)

Unified forge subsystem consolidating forge/modelforge/reward/character/compression/synthetic data runtimes under `mem20rewardforgez/forges/`.

First-class mem20 subsystem for reward forging (linear rewards, shaping, normalization, reward health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20dynamicquestrewardcomposerz`, `mem20realworldimpactrewardsz`, `mem20simz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## Python API (runnable)
```python
from mem20rewardforgez.domain import linear_reward, shaped_reward, normalize, forge_report, probe
print(linear_reward({"a":2},{"a":3}))  # 6
print(shaped_reward(1,0.5))  # 1.5
print(normalize([0,10]))  # [0.0, 1.0]
r=forge_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20rewardforgez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20rewardforgez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20rewardforgez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20rewardforgez serve --port 8818
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/rewardforgez/index.html` (no Vite edits).

## MCP & registration
`RewardForgeToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20rewardforgez/mem20rewardforgez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20rewardforgez
```
Target **7/7**.

## Absorbed: `mem20sensorfusiongatewayz`

# RM-155 — Sensor Fusion Gateway

**Owner:** Andi  
**Lane:** Device, mobile, enrollment, build, and edge delivery

## Outcome
Normalize camera, microphone, motion, location, biometric, and environmental signals

## Breakthrough
Physical context becomes a reusable software capability

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-155 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20temporaldatabasefabricz`

# mem20temporaldatabasefabricz

Bi-temporal memory for mem20. It keeps two things apart that most memory stores
conflate:

- **valid time** — when a claim was true in the world
- **known time** — when *this system* held the belief

The difference matters the moment a fact is learned late, corrected, or
retracted. A store with only a valid axis cannot answer "what did we believe at
noon?" without answering it with today's facts, and cannot distinguish "we
believed this" from "we never knew this".

## The problem it fixes

mem20's `recall_at()` was documented as a bi-temporal query. It was not. It
filtered on a single axis, and it stripped every superseded record *before*
applying the time filter. So asking "what was true at 12:00?" about a fact
learned at 10:00 and corrected at 14:00 returned **nothing** — the pre-correction
truth was unreachable through every query path.

Reproduced, fixed, and locked down by tests in
`memory_engine/tests/test_recall_at_bitemporal.py`.

## Guarantees

- **Corrections never delete.** They close the old version's *known* interval and
  append a new version. Both remain queryable forever.
- **A correction never edits valid time.** The world did not change; only our
  belief about it did.
- **At most one belief per (subject, attribute) is open at a time.** A second
  assertion is refused; use `correct` or `retract`.
- **Half-open intervals `[start, end)`.** The instant a correction lands belongs
  to the correction, not the fact it replaced.
- **Intervals are immutable once written.** Only an interval's open end may be
  closed.
- **Total, deterministic ordering.** Equal queries give byte-identical answers.
- **Idempotent ingest.** Replaying the same ledger adds nothing.
- **Tamper-evident.** Every write appends to a hash-chained event log; `verify`
  re-derives the chain and exits non-zero on any alteration.
- **Content is never duplicated.** A version stores a `value_ref` (a memory
  record id) and a content hash — never a second copy of the text.

## The four slices

Omit an axis to mean *now*; supply one to mean *then*.

| query | slice | reads as |
|---|---|---|
| `get s` | `valid_now_known_now` | current view |
| `get s --valid-at T` | `valid_then_known_now` | what was true at T, judged against everything known today — the **as-of join** |
| `get s --known-at T` | `valid_now_known_then` | what we believed at T that is still true — "were we right?" |
| `get s --valid-at T --known-at T` | `valid_then_known_then` | the historical view |

The slice names the **question**, not the answer. An empty result is an answer,
not a different question.

## CLI

```bash
mem20temporaldatabasefabricz selftest          # prove the core claims, throwaway store
mem20temporaldatabasefabricz put svc.port value 8080 --valid-from T0 --known-at T1
mem20temporaldatabasefabricz correct svc.port value 9090 --known-at T6
mem20temporaldatabasefabricz get svc.port --valid-at T3            # as-of join
mem20temporaldatabasefabricz get svc.port --valid-at T3 --known-at T3   # historical
mem20temporaldatabasefabricz slices svc.port T3    # all four at once
mem20temporaldatabasefabricz history svc.port      # every version, nothing deleted
mem20temporaldatabasefabricz explain svc.port --valid-at T3
mem20temporaldatabasefabricz export --out state.json
mem20temporaldatabasefabricz verify                # non-zero if the chain broke
mem20temporaldatabasefabricz ingest --ledger ~/.mem20/store/ledger.jsonl
```

`--db` selects the SQLite file (default `~/.mem20/temporal/temporal.db`, override
with `MEM20_TEMPORAL_DB`). Output is JSON. Subjects match **exactly** — use the
real topic string; there is no substring matching, because a temporal store
should be precise about which fact it is answering for.

## HTTP surface

```bash
mem20temporaldatabasefabricz serve --port 8791
```

Read and query. Endpoints under `/temporal/*` answer bi-temporal questions;
`/recall/*` proxy the **existing** memory retrieval read-only. This service adds
temporal questions, it does not take over recall.

## How it composes with existing retrieval

Nothing existing was replaced. The ledger stays the single authority for
content, and intervals are *derived* from the append-only ledger that already
exists — so `remember()` and `supersede()` needed no changes and cannot be
bypassed.

```python
from mem20temporaldatabasefabricz.temporal import build_engine, temporal_filter

engine = build_engine(store, memory._load_ledger())
candidates = [r["id"] for r in memory.recall_hybrid("deploy target", k=50)]
current = temporal_filter(engine, candidates, known_at="2026-10-01T00:00:00+00:00")
```

`recall`, `recall_hybrid`, `recall_semantic`, `recall_graph` and the BM25/vector
indexes all remain live and unchanged. The temporal layer restricts and reorders
their output; it never stands in for them.

## Known limitation: conflated valid time on existing data

`memory_engine.remember()` sets `valid_from = now` when a caller supplies no
explicit event time. Every existing mem20 record therefore has
`valid_from == known_from`, so the **valid** axis cannot yet distinguish a
late-arriving fact from a fresh one. This is visible in real data: ingesting the
live ledger yields 374 versions where both axes agree on all of them.

The engine reports this rather than inferring an event time it was never given.
The fix is at the call site — pass `valid_from=` to `remember()` — not something
this package can repair after the fact. New records written with an explicit
`valid_from` are placed correctly on both axes immediately.

## What was removed

The previous version of this package was generated scaffolding: 676 lines whose
"temporal" behaviour was a hardcoded dispatch on integer ids 101–230 returning
canned dictionaries, with 98 dispatch branches and zero tests. Its README
claimed conflict-safe synchronisation, backpressure, failover and a browser
command surface. None of that was implemented, and the claims are gone along
with the code. `selftest` and the test suite are what this package can actually
do.

## Tests

```bash
cd /opt/mem20/mem20temporaldatabasefabricz
python -m pytest tests -q
```

46 tests. Deterministic: an injected clock, no sleeps, no wall-clock waits.

## Absorbed: `mem20universalintegrationcompilerz`

# mem20universalintegrationcompilerz — Universal Integration Compiler

First-class mem20 subsystem for universal integration compilation (compile_integration/validate_mapping/transform/integration_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20protocolautodiscoveryenginez`, `mem20runtimecompatibilityenginez`, `mem20agentoutputcompilerz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20faultcontainmentcellsz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20universalintegrationcompilerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20universalintegrationcompilerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20universalintegrationcompilerz serve --port 8843
```

## Absorbed: `mem20agentoutputcompilerz`

# mem20agentoutputcompilerz — Agent Output Compiler

Merge, deduplicate, compile, validate, and summarize multi-agent outputs, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20agentoutputcompilerz.domain import (
    merge_outputs, dedupe, compile_report, validate_output, summarize, estate_context,
)

outputs = [
    {"agent": "planner", "items": [{"id": 1, "task": "a"}]},
    {"agent": "coder", "items": [{"id": 1, "task": "a"}, {"id": 2, "task": "b"}]},
]
print(merge_outputs(outputs)["sources"])
print(dedupe([{"id": 1}, {"id": 1}, {"id": 2}]))
print(compile_report(outputs))
print(validate_output({"items": []}))
print(summarize(outputs))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20agentoutputcompilerz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20agentoutputcompilerz/mem20agentoutputcompilerz/tests -q
```

## Absorbed: `mem20ambientteamradioz`

# RM-120 — Ambient Team Radio

**Owner:** Sherry  
**Lane:** Human communication, presence, and relationship intelligence

## Outcome
Create lightweight always-available audio presence with intelligent interruption control

## Breakthrough
Distributed teams regain the spontaneity of sharing a room

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-120 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20autonomousdealdeskz`

# mem20autonomousdealdeskz — Autonomous Deal Desk

First-class mem20 subsystem for autonomous deal operations: price deals, score terms, gate approvals, negotiate rounds, and assess deal health. Real runtime with **6 subsystem-specific estate peers** (deal-desk fit — **not** a generic template), SQLite WAL event log, CLI, JSON HTTP API, served cockpit, docs/app integration, and real MCP tools.

## Architecture

- `domain.py` — pure deal ops + `deal_report()`/`probe()`/`estate_context()`
- `ecosystem.py` — 6 adapters (bootstrap); failures reported `{"ok": false, "error": ...}`, never fatal
- `runtime.py` — `Service` + SQLite WAL `EventStore`; CLI; `ThreadingHTTPServer` JSON API; serves `web/`
- `web/` — vanilla operator cockpit (no build)
- `docs/PLAN.md`, `docs/app/autonomousdealdeskz/` estate monitor, gateway entry, MCP mixin

## Ecosystem peers (6, subsystem-specific)

| peer | real functions | role |
|---|---|---|
| `mem20simz` | `revenue`, `profit`, `margin`, `scenario_sim` | deal economics/margin/scenarios |
| `mem20causalroutingbrainz` | `DemandForecastAndCapacityBrain` (observe/forecast/capacity_for) | demand signal & capacity headroom |
| `mem20acquisitionandpartnershipscoutz` | `target_score`, `strategic_fit`, `rank_targets`, `synergy_estimate` | partnership/strategic fit & synergy |
| `mem20antiexploitationrewardshieldz` | `RewardShield.evaluate`/`exploit_ratio` | approval guardrail/corroboration |
| `mem20capabilitymarketplacez` | `CapabilityMarketplace` (add/locate/distribution) | capability routing via consistent hashing |
| `mem20autonomoussaleslaboratoryz` | `pipeline_value`, `conversion_probability`, `segment_leads` | pipeline value/conversion/segments |

## Python API

```python
from mem20autonomousdealdeskz.domain import (
    price_deal, terms_score, approval_required, negotiate_round, deal_health,
    deal_report, probe, estate_context,
)

print(price_deal({"price": 1000}, {"volume": 500}))
print(terms_score({"payment_days": 15, "contract_months": 12, "auto_renew": True}))
print(approval_required(9500, threshold=10000))
print(negotiate_round(1000, 850, rounds_left=2))
print(deal_health({"signed": True, "paid": False}))

report = deal_report(product={"price": 1200}, customer={"volume": 400}, deal={"deal_value": 1100})
print(report["ok"], report["price"], len(report["peers"]))  # True, ..., 6
print(probe()["ok"])  # True (all peers reachable)
```

## CLI

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz serve --port 8782
```

## HTTP API & web cockpit

`GET/POST /api/status`, `GET/POST /api/doctor`, `POST /api/simulate`, `POST /api/price`, `POST /api/negotiate`, `GET /api/events`, `GET /api/health`. Cockpit served at `/` (static `web/`, no build). State: `~/.mem20/autonomousdealdeskz/state.sqlite3` (SQLite WAL) or `--store`/`MEM20_DEALDESK_STORE`.

```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz serve --port 8782
# cockpit: http://127.0.0.1:8782/  |  estate monitor: docs/app/autonomousdealdeskz/index.html
```

## MCP & registration

MCP: `AutonomousDealDeskToolsMixin` (`mcp/tools/mem20autonomousdealdeskz_tools.py`) registered in `mcp/server.py` (`autonomousdealdeskz_status|doctor|price`). Gateway: `gateway/mem20_gateway.py` SUBSYSTEMS entry. docs/app linked from `docs/app/README.md` (no compiled Vite assets edited).

## Tests & conformance

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20autonomousdealdeskz/mem20autonomousdealdeskz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20autonomousdealdeskz
node --check mem20autonomousdealdeskz/mem20autonomousdealdeskz/web/app.js
```

Target: **7/7**.

## Limits

- Pricing/negotiation logic is deterministic rules for this subsystem; real commercial/legal/ERP integrations are target-environment concerns.
- Peer unavailability is surfaced in report/probe and does not crash core operations.

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

## Absorbed: `mem20autonomoussoftwarefoundryz`

# mem20autonomoussoftwarefoundryz — Autonomous Software Foundry

First-class mem20 subsystem that turns software specs into actionable build plans: decompose specs into tasks, score code quality, make deploy decisions, estimate effort, and produce build artifacts. It runs as a real service with **6 software-foundry-specific estate peers** (no generic template), a SQLite WAL event log, a CLI, a JSON HTTP API, a served operator cockpit, docs/app estate integration, and real MCP tools.

## At a glance

| item | value |
|---|---|
| package | `mem20autonomoussoftwarefoundryz` |
| console entry | `mem20autonomoussoftwarefoundryz` / `python -m mem20autonomoussoftwarefoundryz` |
| core modules | `domain.py`, `ecosystem.py`, `runtime.py` |
| web cockpit | `web/index.html`, `web/style.css`, `web/app.js` (served by runtime, no build step) |
| state | SQLite WAL `events` table (`~/.mem20/autonomoussoftwarefoundryz/state.sqlite3` or `--store` / `MEM20_SWFOUNDRY_STORE`) |
| cross-subsystem peers | 6, each called on the normal report/probe path with real APIs |
| registrations | `gateway/mem20_gateway.py` SUBSYSTEMS, `mcp/tools/mem20autonomoussoftwarefoundryz_tools.py` wired in `mcp/server.py`, `docs/app/autonomoussoftwarefoundryz/` linked from `docs/app/README.md` |
| conformance target | 7/7 |

## Architecture

- `domain.py` — pure foundry operations plus `foundry_report()`, `probe()`, and `estate_context()` (the report aggregates real peer results).
- `ecosystem.py` — the 6 peer adapters (bootstraps peer package paths). Every adapter calls real peer APIs and returns computed results; failures are reported as `{"ok": false, "subsystem": ..., "error": ...}` and never crash core operations.
- `runtime.py` — `Service` + SQLite WAL `EventStore`; argparse CLI; `ThreadingHTTPServer` JSON API that also serves the static `web/` cockpit with path-traversal protection and CORS headers.
- `web/` — vanilla operator cockpit (no compiled assets).
- `docs/PLAN.md` — depth-first delivery record.
- `docs/app/autonomoussoftwarefoundryz/index.html` — estate-shell monitor (static; no Vite asset edits), linking back to this README and `docs/app/README.md`.

## Domain model

| function | behavior |
|---|---|
| `spec_to_tasks(spec)` | expands `spec["features"]` into per-feature `todo` tasks and always adds `tests` + `deploy` tasks |
| `code_quality(metrics)` | scores 0–1.0: `+0.4` tests pass, `+0.3` coverage ≥ 0.8, `+0.3` lint clean (rounded to 3 decimals) |
| `deploy_decision(quality, threshold=0.7)` | boolean gate on quality |
| `estimate_effort(spec)` | `days = 2 * feature_count`; complexity `low`/`medium`/`high` |
| `build_artifact(spec, code)` | deterministic artifact record: name, `0.1.0`, 12-char SHA-256 checksum, line count |
| `foundry_report(...)` | computes core outputs and calls all 6 peers; `ok` is true only when every peer reports `ok` |
| `probe()` | runs the 6 peer probes and aggregates reachability |
| `estate_context(store_path=None)` | lightweight estate summary (`engine_status_checked`, `peer_count`, `peers_ok`, `checks`) |

## Ecosystem peers (6, software-foundry specific)

These peers were chosen for the *software foundry* job (build/tooling, versioned artifacts, build telemetry, safe deploys, spec quality, build economics). The set is different from other subsystems’ peer sets.

| peer | real functions/classes used | role in this subsystem |
|---|---|---|
| `mem20capabilitymarketplacez` | `CapabilityMarketplace(replicas=32)`, `add`, `locate`, `distribution` | route a build key to a tool/capability owner via consistent hashing and report distribution |
| `mem20pipez` | `version_asset`, `recover`, `vc_health` | version an artifact, recover a target version, and report version-control health |
| `mem20eventstreamsuperhighwayz` | `create_stream`, `publish`, `throughput` | publish build/foundry events to a stream and report throughput |
| `mem20faultcontainmentcellsz` | `FaultContainmentCells`, `CircuitOpen`, `call` | contain deploy execution behind a circuit breaker; open-circuit is reported, not fatal |
| `mem20loreragcontentgeneratorz` | `generate`, `rank_adapters`, `quality_score` | assess/spec-generate quality for a build prompt and select/rank adapters |
| `mem20simz` | `revenue`, `profit`, `margin`, `scenario_sim` | model effort economics (profit/margin/scenario periods) for the estimated build |

## Python API (runnable)

```python
from mem20autonomoussoftwarefoundryz.domain import (
    build_artifact,
    code_quality,
    deploy_decision,
    estate_context,
    estimate_effort,
    foundry_report,
    probe,
    spec_to_tasks,
)

spec = {"name": "app", "features": ["auth", "api"]}
metrics = {"tests_pass": True, "coverage": 0.9, "lint_clean": True}
code = "print('hi')\n"

tasks = spec_to_tasks(spec)
quality = code_quality(metrics)
print(len(tasks), quality, deploy_decision(quality))  # 4 1.0 True
print(estimate_effort(spec))                           # {'days': 4, 'complexity': 'low'}
print(build_artifact(spec, code)["checksum"])          # 12-char sha256 prefix

report = foundry_report(spec=spec, code=code, metrics=metrics)
print(report["ok"], report["quality"], report["deploy"], len(report["peers"]))  # 6 peers

p = probe()
print(p["ok"], sorted(p["checks"].keys()))

ctx = estate_context()
print(ctx["engine_status_checked"], ctx["peer_count"])  # True 6
```

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussoftwarefoundryz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussoftwarefoundryz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussoftwarefoundryz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussoftwarefoundryz simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussoftwarefoundryz serve --port 8786
```

`--store PATH` (or `MEM20_SWFOUNDRY_STORE`) selects the SQLite state file.

## HTTP API and web cockpit

The runtime serves a JSON API and the static cockpit at `/` (no separate frontend build).

| method | route | purpose |
|---|---|---|
| GET | `/api/health` | service health |
| GET/POST | `/api/status` | foundry report (POST accepts `spec`, `code`, `metrics`) |
| GET/POST | `/api/doctor` | peer probe |
| POST | `/api/simulate` | run internal scenarios (tasks/report/doctor) |
| POST | `/api/quality` | compute `code_quality` for posted `metrics` |
| GET | `/api/events?since=&limit=` | recent WAL event records |

```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussoftwarefoundryz serve --port 8786
# cockpit:        http://127.0.0.1:8786/
# estate monitor: docs/app/autonomoussoftwarefoundryz/index.html (set API base to the server)
```

## MCP and registration

- MCP mixin: `AutonomousSoftwareFoundryToolsMixin` (`mcp/tools/mem20autonomoussoftwarefoundryz_tools.py`), wired/registered in `mcp/server.py` as `autonomoussoftwarefoundryz_status` and `autonomoussoftwarefoundryz_doctor` (lazy/guarded import pattern).
- Gateway: `gateway/mem20_gateway.py` `SUBSYSTEMS["mem20autonomoussoftwarefoundryz"]` with purpose, working entry, owner, wave.
- Docs/app: `docs/app/autonomoussoftwarefoundryz/index.html` linked from `docs/app/README.md` (static HTML; no compiled Vite assets edited).

## Tests and conformance

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20autonomoussoftwarefoundryz/mem20autonomoussoftwarefoundryz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20autonomoussoftwarefoundryz
node --check mem20autonomoussoftwarefoundryz/mem20autonomoussoftwarefoundryz/web/app.js
```

Target: **7/7** conformance (real domain, no stubs, real-value tests, CLI, runnable README examples, >=5 cross-module imports+calls on covered lines, MCP/gateway registration).

## Limits

- Build quality/deploy/effort logic is deterministic and local to this subsystem; real CI/CD, source hosting, artifact registries, and production deploy systems are target-environment integrations.
- Peer unavailability is surfaced in `foundry_report`/`probe`/`doctor` (and via MCP) rather than crashing core operations.
- The web cockpit and docs/app monitor are static frontends against the local HTTP API; they require the runtime server to be running.

## Absorbed: `mem20autonomoustrafficcontrollerz`

# RM-190 — Autonomous Traffic Controller

**Owner:** Ariel  
**Lane:** Mission dispatch, execution visibility, and real-time operations

## Outcome
Prevent queue congestion, cascading retries, and resource gridlock across runtimes

## Breakthrough
High-scale agent traffic remains stable under pressure

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-190 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20batteryawareagentschedulerz`

# RM-159 — Battery-Aware Agent Scheduler

**Owner:** Andi  
**Lane:** Device, mobile, enrollment, build, and edge delivery

## Outcome
Run jobs according to battery state, thermal headroom, urgency, and charging patterns

## Breakthrough
Local AI becomes practical without destroying battery life

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-159 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20crossplatformmicrokernelz`

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

## Absorbed: `mem20edgetocloudintelligencecontinuumz`

# mem20edgetocloudintelligencecontinuumz — Edge-to-Cloud Intelligence Continuum (RM-214)

**Outcome:** run one workload fluidly across local devices, private servers, peers, and paid clouds.  
**Breakthrough:** compute placement becomes invisible, resilient, and cost-aware.

This subsystem is a real, first-class continuum control plane: typed domain logic, a durable SQLite WAL state plane, a service that owns placement/dispatch/failover, cross-subsystem judgements from six **unique** peers (a different set from `mem20causalroutingbrainz`), a CLI, a JSON HTTP API, a served operator cockpit, and a `docs/app` monitor.

## What it does

- **Invisible placement:** callers declare constraints (`required_capabilities`, latency/cost ceilings, privacy zone, resilience, preferred tiers, priority, size) — not machine names. The scheduler scores feasible targets across `local`, `edge`, `private`, `peer`, and `cloud`.
- **Resilient execution:** failed/degraded/draining sources produce explicit migration/failover plans. Migration semantics are verified through the zero-downtime migration brain (unverified cutover is refused/rolled back in the semantic check).
- **Cost-aware:** execution cost, egress/transport cost, pipeline economics, and market signals influence placement and are returned in decisions.
- **Honest decisions:** every placement returns the chosen target, score, confidence, components/weights, alternatives, and bottlenecks. Peer signals are reported (fail-open) — never hidden.

## Architecture

| Layer | File | Responsibility |
|---|---|---|
| Domain | `mem20edgetocloudintelligencecontinuumz/domain.py` | Tiers/status/state enums, `Target`/`Workload` validation and capacity accounting, latency/cost/privacy/capability checks, weighted scoring, `place_workload`, `failover_plan`, `migration_plan`, `continuum_health`. Pure (no I/O). |
| State plane | `mem20edgetocloudintelligencecontinuumz/store.py` | SQLite WAL: versioned targets/workloads, append-only placements, migrations, ordered events, snapshots/restore, idempotency keys, conflict detection. |
| Ecosystem | `mem20edgetocloudintelligencecontinuumz/ecosystem.py` | Six unique peer adapters with real calls and fail-open reporting. |
| Service | `mem20edgetocloudintelligencecontinuumz/service.py` | Target registry, submit/place/dispatch/complete, failover, migration planning, status/events/metrics/snapshot/restore, `doctor`/`simulate`/`benchmark`. |
| Runtime | `mem20edgetocloudintelligencecontinuumz/runtime.py` | CLI + `ThreadingHTTPServer` JSON API + static cockpit (`web/`), CORS, error mapping (`ValidationError`→400, `NotFoundError`→404, `ConflictError`→409). |
| Web | `mem20edgetocloudintelligencecontinuumz/web/` | Operator cockpit: targets, workloads, dispatch/failover, events, doctor/simulate. |

## Unique cross-subsystem wiring (criterion 6)

**Rule:** the ≥5 cross-module peers must be a **different set on each subsystem** (no reused template). This subsystem uses a continuum-specific set, different from `mem20causalroutingbrainz`:

| Peer | Real calls used | What it contributes |
|---|---|---|
| `mem20federatedresearchgridz` | `register_node`, `distribute_task`, `federated_round`, `grid_health` | Federated task distribution/health across continuum tiers |
| `mem20pipez` | `stage_cost`, `pipeline_cost`, `bottleneck`, `optimize_throughput`, `cost_breakdown` | Cost-aware pipeline/placement economics |
| `mem20edgetransportfabricz` | `route_path`, `qos_class`, `allocate_bandwidth`, `transport_health` | Transport path, QoS class, bandwidth allocation/health |
| `mem20causalroutingbrainz` | `ZeroDowntimeMigrationBrain.begin`, `write/read`, `verify_and_cutover`/rollback semantics | Verified zero-downtime migration semantics (refuse unverified cutover) |
| `mem20globalcapabilitymarketplacez` | `list_capability`, `search_marketplace`, `match`, `transaction`, `marketplace_health` | Capability discovery/matching across tiers/providers |
| `mem20resourceexchangemarketz` | `list_resource`, `buy`, `price_history`, `market_health` | Resource pricing/market signals |

All are invoked on normal service paths (register/submit/place/dispatch/status/doctor) and exercised by the subsystem’s tests.

## CLI

```bash
python -m mem20edgetocloudintelligencecontinuumz --store /tmp/ctm.db status
python -m mem20edgetocloudintelligencecontinuumz --store /tmp/ctm.db doctor
python -m mem20edgetocloudintelligencecontinuumz --store /tmp/ctm.db simulate
python -m mem20edgetocloudintelligencecontinuumz --store /tmp/ctm.db benchmark --iterations 20
python -m mem20edgetocloudintelligencecontinuumz --store /tmp/ctm.db target add --id local-lab --tier local --cpu 8 --memory 16 --latency 2 --cost 0 --bandwidth 10000 --capabilities compute,render
python -m mem20edgetocloudintelligencecontinuumz --store /tmp/ctm.db target add --id cloud-gpu --tier cloud --cpu 32 --memory 64 --latency 90 --cost 0.4 --bandwidth 10000 --capabilities compute,gpu,render
python -m mem20edgetocloudintelligencecontinuumz --store /tmp/ctm.db target list
python -m mem20edgetocloudintelligencecontinuumz --store /tmp/ctm.db workload submit --id render-1 --cpu 2 --memory 4 --size 0.5 --capabilities render --max-latency 200 --resilience high
python -m mem20edgetocloudintelligencecontinuumz --store /tmp/ctm.db dispatch --id render-1
python -m mem20edgetocloudintelligencecontinuumz --store /tmp/ctm.db workload complete render-1 --reason done
python -m mem20edgetocloudintelligencecontinuumz --store /tmp/ctm.db failover render-1 --reason outage
python -m mem20edgetocloudintelligencecontinuumz --store /tmp/ctm.db events --limit 20
python -m mem20edgetocloudintelligencecontinuumz --store /tmp/ctm.db snapshot --label before-change
python -m mem20edgetocloudintelligencecontinuumz --store /tmp/ctm.db serve --host 127.0.0.1 --port 8791
```

## Runnable example (verified)

```bash
cd /opt/mem20
S=/tmp/ctm-demo.db
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20edgetocloudintelligencecontinuumz --store "$S" \
  target add --id local-lab --tier local --cpu 8 --memory 16 --latency 2 --cost 0 --bandwidth 10000 --capabilities compute,render
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20edgetocloudintelligencecontinuumz --store "$S" \
  target add --id cloud-gpu --tier cloud --cpu 32 --memory 64 --latency 90 --cost 0.4 --bandwidth 10000 --capabilities compute,gpu,render
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20edgetocloudintelligencecontinuumz --store "$S" \
  workload submit --id render-1 --cpu 2 --memory 4 --size 0.5 --capabilities render --max-latency 200 --resilience high
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20edgetocloudintelligencecontinuumz --store "$S" \
  dispatch --id render-1
```

Observed (real run, key fields):

```text
submit: ok=True chosen_preview=local-lab score=0.992454
signals: federated/cost/resource_market all ok
dispatch: 1 chosen=local-lab state=running
peer_signals: federated/cost/capability_market/resource_market/transport all ok
migration_semantics: phase=cutover verified=True
```

`submit` returns a full `placement_preview` (chosen, score, confidence, feasible alternatives, components, bottlenecks) plus federated/cost/resource market signals. `dispatch` reserves capacity, runs the workload, records the placement, and returns transport/capability/resource/federated/cost signals and migration semantics. The cloud target remains a feasible alternative (visible in the decision) but local wins on latency/cost for this constraint set.

## HTTP API

The server (`serve`) hosts the same JSON API and the static cockpit at `/`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/status` | continuum health, tiers, metrics, transport signal |
| GET | `/api/targets`, `/api/targets/{id}` | targets |
| POST | `/api/targets` | register target |
| POST | `/api/targets/{id}/status` | set target status |
| DELETE | `/api/targets/{id}` | delete target |
| GET/POST | `/api/workloads`, `/api/workloads/{id}` | list/get/submit workloads |
| POST | `/api/dispatch` | dispatch queued/specific workload (`workload_id`, `limit`) |
| POST | `/api/place` | compute/place a workload |
| POST | `/api/complete` | complete/fail (`workload_id`, `success`, `reason`) |
| POST | `/api/failover` | migrate/fail over a workload |
| POST | `/api/migrations/plan` | plan migrations for overloaded/degraded sources |
| GET | `/api/events?since=&limit=` | ordered event stream |
| GET | `/api/placements?workload_id=` | placement journal |
| GET | `/api/metrics`, `/api/doctor`, `/api/benchmark?iterations=` | observability and peer probe |
| POST | `/api/snapshot`, `/api/restore`, `/api/simulate` | state management / scenario run |

Errors are JSON with real status codes (400 validation, 404 missing, 409 conflict).

## Web surfaces

- **Per-subsystem cockpit:** served from the continuum process at `GET /` (`web/index.html`, `app.js`, `style.css`).
- **docs/app integration:** `docs/app/continuum/index.html` — a static estate monitor that connects to the continuum API (`?api=` / stored base URL) and shows health, targets, workloads, and peer/doctor status. Linked from `docs/app/README.md`. (Compiled Vite assets in `docs/app` are not modified.)

## State, safety, and resilience

- SQLite WAL state plane with version checks/conflict errors, append-only placements/events, idempotent submissions, and snapshots/restore.
- Placement enforces capability, privacy zone, capacity, max latency, and max cost; infeasible results include bottlenecks.
- Failover produces explicit plans; migration semantics are checked via `mem20causalroutingbrainz` and refuse unverified cutover / report rollback.
- Cross-subsystem failures are reported as `ok:false` signals; they do not fabricate placement success.

## Tests

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20edgetocloudintelligencecontinuumz -q
```

Covers domain scoring/constraints/failover/health, store versioning/events/snapshots/idempotency, all six ecosystem adapters (real calls), service lifecycle/dispatch/failover/privacy/cost/simulate/doctor, runtime CLI, and HTTP API + static cockpit/error mapping.

## Conformance

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20edgetocloudintelligencecontinuumz
```

Target: 7/7 — real domain logic (no stubs), tests, CLI, runnable README example, >=5 cross-modules imported and called on covered lines, gateway/MCP registration.

## Limits (honest)

- Named live production provider credentials, real paid-cloud/device fleets, and governed FreeStack production deployment are target-environment integrations not claimed complete.
- The transport/cost/market/federated signals are real peer computations over the current model; they do not replace provider-specific billing, IAM, or network control planes.
- Migration is modeled as verified semantic cutover plus state movement in the continuum plane; application-specific data replication is delegated to the workload/integration.

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

## Absorbed: `mem20hardwareawareinferencecompilerz`

# mem20hardwareawareinferencecompilerz — Hardware-Aware Inference Compiler (RM-065, #322)

**Outcome:** compile model graphs for the exact CPU, GPU, NPU, memory, and latency budget available.

Preserves legacy domain API (**#314 peer dependency**) and CAPABILITY Engine/CLI/10-scenario simulator. `search` is meaningful for compile payloads and backward-compatible for generic search.

## Legacy domain API (preserved)
`fuse_ops(ops)`, `quantize(weights,bits=8)`, `schedule(ops,device)`, `memory_estimate(ops,dtype_bytes=4)`, `optimize_graph(graph)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Compile role |
|---|---|---|
| `mem20causalroutingbrainz` | `Node`,`Workload`,`estimate_energy_wh`,`estimate_cost`,`score_placement` | hardware target energy/cost/placement |
| `mem20modalitybridgez` | `supported_modalities`,`encode_text`,`bridge` | model/modality context |
| `mem20labz` | `create_genome`,`fitness`,`mutate` | model variant evaluation |
| `mem20personalmodelevolutionz` | `create_model`,`adapt`,`predict` | device/user adaptation signal |
| `mem20pipez` | `pathfind`,`validate_level` | graph traversal/validation |
| `mem20pipez` | `parse_dialogue`,`validate_dialogue`,`export_script` | artifact spec validation/export |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hardwareawareinferencecompilerz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hardwareawareinferencecompilerz execute '{"compile":true,"ops":[{"type":"matmul","size":10,"priority":1},{"type":"relu","size":10}],"weights":[0.0,0.5,1.0],"device":{"id":"cpu"}}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hardwareawareinferencecompilerz serve --port 8802
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20hardwareawareinferencecompilerz/tests mem20hardwareawareinferencecompilerz/mem20hardwareawareinferencecompilerz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20hardwareawareinferencecompilerz
```

## Absorbed: `mem20loreragcontentgeneratorz`

# mem20loreragcontentgeneratorz — LoRA RAG Content Generator

Retrieval-augmented generation helpers with optional **grounded retrieval** via `memory_engine` (and local keyword fallback). Integrates with mem20 estate modules for conformance.

## Python API

```python
import tempfile
from pathlib import Path
from memory_engine import EngineConfig, MemoryEngine
from mem20loreragcontentgeneratorz.domain import retrieve, retrieve_from_memory, generate, estate_context

# Local corpus
docs = [{"text": "dragons live in caves"}, {"text": "elves love forests"}]
ctx = retrieve(docs, "dragon caves", k=1)
print(generate(ctx, "tell me")["output"])

# Grounded in memory_engine
with tempfile.TemporaryDirectory() as d:
    eng = MemoryEngine(EngineConfig(store_path=Path(d).resolve()))
    eng.remember("lore", "The ancient dragon guards the crystal cave.", epistemic_status="observed")
    grounded = retrieve_from_memory("dragon cave", store_path=d, k=3)
    print(generate(grounded, "describe the guardian")["grounded"])
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20loreragcontentgeneratorz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20loreragcontentgeneratorz/mem20loreragcontentgeneratorz/tests -q
```

## Absorbed: `mem20realtimeeventautopilotz`

# mem20realtimeeventautopilotz — Real-Time Event Autopilot

First-class mem20 subsystem for real-time event autopilot (event ingestion, rule evaluation, automated actions, throttling) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20selfhealingplansz`, `mem20causalroutingbrainz`, `mem20universalhealthnervoussystemz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20realtimeeventautopilotz.domain import ingest_event, evaluate_rules, autopilot, throttle, autopilot_report, probe
s={}; ingest_event(s,{"severity":9})
acts=evaluate_rules({"severity":9}, [{"condition":lambda e:e["severity"]>5,"action":"notify"}])
print(acts)  # ['notify']
r=autopilot_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeeventautopilotz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeeventautopilotz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeeventautopilotz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeeventautopilotz serve --port 8812
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/realtimeeventautopilotz/index.html` (no Vite edits).

## MCP & registration
`RealTimeEventAutopilotToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20realtimeeventautopilotz/mem20realtimeeventautopilotz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20realtimeeventautopilotz
```
Target **7/7**.

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

## Absorbed: `mem20secretslessworkloadidentityz`

# mem20secretslessworkloadidentityz — Secrets-less Workload Identity

First-class mem20 subsystem for secrets-less workload identity (issue/verify/rotate identities, health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20universalhealthnervoussystemz`, `mem20faultcontainmentcellsz`, `mem20selfhealingplansz`, `mem20deterministicconfigurationgraphz`.

## Python API (runnable)
```python
from mem20secretslessworkloadidentityz.domain import issue_identity, verify, rotate, identity_report, probe
i=issue_identity("svc"); print(verify(i)["valid"])  # True
print(rotate(i)["workload"])  # svc
r=identity_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20secretslessworkloadidentityz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20secretslessworkloadidentityz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20secretslessworkloadidentityz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20secretslessworkloadidentityz serve --port 8823
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/secretslessworkloadidentityz/index.html` (no Vite edits).

## MCP & registration
`SecretslessWorkloadIdentityToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20secretslessworkloadidentityz/mem20secretslessworkloadidentityz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20secretslessworkloadidentityz
```
Target **7/7**.

## Absorbed: `mem20selftuningresourcegovernorz`

# mem20selftuningresourcegovernorz — Self-Tuning Resource Governor

First-class mem20 subsystem for self-tuning resource governance (govern/adjust_quota/governor_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20causalroutingbrainz`, `mem20causalroutingbrainz`, `mem20faultcontainmentcellsz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20autonomousrecoverydirectorz`.

## Python API (runnable)
```python
from mem20selftuningresourcegovernorz.domain import govern, adjust_quota, governor_report, probe
print(govern({"c":100},{"c":90},{"c":0.8})[0]["action"])  # throttle
print(adjust_quota("c",100,0.9))  # 120.0
r=governor_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selftuningresourcegovernorz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selftuningresourcegovernorz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selftuningresourcegovernorz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selftuningresourcegovernorz serve --port 8827
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/selftuningresourcegovernorz/index.html` (no Vite edits).

## MCP & registration
`SelfTuningResourceGovernorToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20selftuningresourcegovernorz/mem20selftuningresourcegovernorz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20selftuningresourcegovernorz
```
Target **7/7**.

## Absorbed: `mem20sensorymemoryingestz`

# mem20sensorymemoryingestz — Sensory Memory Ingest

First-class mem20 subsystem for sensory memory ingest (ingest/filter_by_modality/recent/ingest_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20episodicmemorygraphz`, `mem20eventstreamsuperhighwayz`, `mem20rewardforgez`, `mem20capabilitymarketplacez`, `mem20universalhealthnervoussystemz`, `mem20faultcontainmentcellsz`.

## Python API (runnable)
```python
from mem20sensorymemoryingestz.domain import ingest, filter_by_modality, recent, ingest_health, ingest_report, probe
s={"entries":[]}; ingest(s,"hi","text"); print(ingest_health(s)["entries"])  # 1
r=ingest_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20sensorymemoryingestz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20sensorymemoryingestz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20sensorymemoryingestz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20sensorymemoryingestz serve --port 8829
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/sensorymemoryingestz/index.html` (no Vite edits).

## MCP & registration
`SensoryMemoryIngestToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20sensorymemoryingestz/mem20sensorymemoryingestz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20sensorymemoryingestz
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
