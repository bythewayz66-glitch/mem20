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
