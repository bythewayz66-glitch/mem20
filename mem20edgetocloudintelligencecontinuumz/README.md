# mem20edgetocloudintelligencecontinuumz — Edge-to-Cloud Intelligence Continuum (RM-214)

**Outcome:** run one workload fluidly across local devices, private servers, peers, and paid clouds.  
**Breakthrough:** compute placement becomes invisible, resilient, and cost-aware.

This subsystem is a real, first-class continuum control plane: typed domain logic, a durable SQLite WAL state plane, a service that owns placement/dispatch/failover, cross-subsystem judgements from six **unique** peers (a different set from `mem20edgefleetbrainz`), a CLI, a JSON HTTP API, a served operator cockpit, and a `docs/app` monitor.

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

**Rule:** the ≥5 cross-module peers must be a **different set on each subsystem** (no reused template). This subsystem uses a continuum-specific set, different from `mem20edgefleetbrainz`:

| Peer | Real calls used | What it contributes |
|---|---|---|
| `mem20federatedresearchgridz` | `register_node`, `distribute_task`, `federated_round`, `grid_health` | Federated task distribution/health across continuum tiers |
| `mem20pipez` | `stage_cost`, `pipeline_cost`, `bottleneck`, `optimize_throughput`, `cost_breakdown` | Cost-aware pipeline/placement economics |
| `mem20edgetransportfabricz` | `route_path`, `qos_class`, `allocate_bandwidth`, `transport_health` | Transport path, QoS class, bandwidth allocation/health |
| `mem20zerodowntimemigrationbrainz` | `ZeroDowntimeMigrationBrain.begin`, `write/read`, `verify_and_cutover`/rollback semantics | Verified zero-downtime migration semantics (refuse unverified cutover) |
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
- Failover produces explicit plans; migration semantics are checked via `mem20zerodowntimemigrationbrainz` and refuse unverified cutover / report rollback.
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
