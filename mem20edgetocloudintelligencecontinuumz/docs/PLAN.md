# Edge-to-Cloud Intelligence Continuum — implementation plan (RM-214)

## Goal
Run one workload fluidly across local devices, private servers, peers, and paid
clouds. Make placement **invisible** (constraints, not machine names),
**resilient** (verified migration/failover with rollback-safe semantics), and
**cost-aware** (execution + transport + market signals).

## Delivered architecture

| layer | module | responsibility |
|---|---|---|
| Domain | `domain.py` | Tiers (local/edge/private/peer/cloud), targets, workloads, validation, capacity/latency/cost/privacy estimates, weighted placement, failover/migration plans, continuum health. Pure, no I/O. |
| State plane | `store.py` | SQLite WAL. Versioned targets/workloads, append-only placements, migrations, ordered events, snapshots/restore, idempotency keys. |
| Ecosystem | `ecosystem.py` | Six **unique** peer adapters (different set from mem20edgefleetbrainz): federated grid, AI pipeline cost, edge transport fabric, zero-downtime migration brain, global capability marketplace, resource exchange market. Real calls, fail-open reporting. |
| Service | `service.py` | Target registry, workload submit/place/dispatch/complete, failover, migration planning, status/events/snapshots, doctor/simulate/benchmark. All writes via store. |
| Runtime | `runtime.py` | CLI (`status/doctor/simulate/benchmark/target/workload/dispatch/place/failover/migrations-plan/snapshot/restore/serve`), JSON HTTP API, static cockpit, CORS, real error mapping (400/404/409). |
| Web | `web/` | Served operator cockpit (targets, workloads, dispatch/failover, events, doctor/simulate). |
| Tests | `tests/` | Domain, store, ecosystem, service, runtime/CLI, HTTP — 27+ real assertions exercising peer integrations on covered lines. |

## Unique cross-subsystem peers (criterion 6)

1. `mem20federatedresearchgridz` — `register_node`, `distribute_task`, `federated_round`, `grid_health`
2. `mem20aipipelinecostoptimizerz` — `stage_cost`, `pipeline_cost`, `bottleneck`, `optimize_throughput`, `cost_breakdown`
3. `mem20edgetransportfabricz` — `route_path`, `qos_class`, `allocate_bandwidth`, `transport_health`
4. `mem20zerodowntimemigrationbrainz` — `ZeroDowntimeMigrationBrain.begin/verify_and_cutover/rollback`
5. `mem20globalcapabilitymarketplacez` — `list_capability`, `search_marketplace`, `match`, `transaction`, `marketplace_health`
6. `mem20resourceexchangemarketz` — `list_resource`, `buy`, `price_history`, `market_health`

This set is intentionally different from mem20edgefleetbrainz and must remain different from future subsystems.

## Key behaviors

- Capability/privacy/latency/cost/capacity are enforced; infeasible placements return explicit bottlenecks.
- Cross-system peer signals add bounded bonuses/penalties and are reported (never hidden).
- Migration semantics refuse unverified cutover and roll back when parity cannot be proven (via zero-downtime migration brain).
- Idempotent submission, version/conflict checks, append-only placement/event history, snapshots/restore.

## Verification

- `python -m pytest mem20edgetocloudintelligencecontinuumz -q` passes.
- `python -m mem20edgetocloudintelligencecontinuumz simulate` passes all scenarios.
- `python -m mem20edgetocloudintelligencecontinuumz doctor` reaches all 6 peers.
- `scripts/renovation/conformance.py mem20edgetocloudintelligencecontinuumz` reports 7/7.
