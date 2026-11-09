# Edge Transport Fabric (RM-077) — implementation plan

## Goal
Move bounded data and commands across intermittently connected nodes so devices
and remote sites remain integrated even with poor connectivity.

## Delivered architecture

| layer | module | responsibility |
|---|---|---|
| Domain | `domain.py` | Legacy-compatible transport primitives (`route_path`, `qos_class`, `allocate_bandwidth`, `transport_health`) plus advanced fabric model: `FabricNode`/`FabricLink`/`FlowDemand`/`PathDecision`, bandwidth-aware shortest path, QoS/SLA classification, admission, reservations, congestion/health, reroute planning, intermittent-connectivity handling. Pure. |
| State plane | `store.py` | SQLite WAL. Versioned nodes/links/flows, append-only events, placement journal, snapshots/restore, idempotency keys. |
| Ecosystem | `ecosystem.py` | Six **unique** transport-relevant peer adapters (different set from #300 and #301): self-healing mesh retries, traffic admission/backpressure, fault containment/circuit breaking, causal routing influence, recovery planning, event-stream telemetry. Real calls, fail-open reporting. |
| Service | `service.py` | Topology CRUD, flow admit/route/reserve/release/reroute, status/doctor/events/placements/snapshots, simulate/benchmark. Peer signals attached to real operations. |
| Runtime | `runtime.py` | CLI (`status/doctor/simulate/benchmark/node/link/flow/events/placements/snapshot/restore/serve/...`, legacy `execute`), JSON HTTP API, static cockpit (`web/`), CORS, error mapping (400/404/409). |
| Web | `web/` | Served operator cockpit (health, nodes/links/flows, admit/route, doctor/simulate, events). |

## Unique cross-subsystem peers (criterion 6)
1. `mem20meshz.mem20meshz.meshes.selfhealing.domain.SelfHealingConnectorMesh` — resilient transient delivery/retry.
2. `mem20autonomoustrafficcontrollerz.domain.TokenBucket/LeakyBucket` — admission control/backpressure.
3. `mem20faultcontainmentcellsz.domain.FaultContainmentCells` — circuit breaking/fail-fast containment.
4. `mem20causalroutingbrainz.domain` — `route_by_cause`/`causal_effect`/`confounder_adjust`/`intervention_value`.
5. `mem20autonomousrecoverydirectorz.domain` — `triage`/`rollback_plan`/`remediate`/`recovery_time`/`health_after`.
6. `mem20eventstreamsuperhighwayz.domain` — `create_stream/publish/subscribe/consume/throughput/lag` telemetry.

This set is intentionally different from mem20causalroutingbrainz (#300) and
mem20edgetocloudintelligencecontinuumz (#301).

## Compatibility
Legacy domain API remains compatible for existing callers (e.g.
`mem20edgetocloudintelligencecontinuumz`): `route_path(src,dst,nodes)` with
neighbor-map nodes, `qos_class`, `allocate_bandwidth`, `transport_health`.

## Verification
- `python -m pytest mem20edgetransportfabricz/tests -q` passes.
- `python -m mem20edgetransportfabricz simulate` / `doctor` return real results.
- `scripts/renovation/conformance.py mem20edgetransportfabricz` reports 7/7.

## Limits
- No claim of production mesh radios, provider SD-WAN, real device drivers, or
  managed global control plane. Transport is modeled as bounded routing/QoS/
  bandwidth/link-state decisions over declared topology; application payload
  replication/store-and-forward is delegated to callers/integrations.
