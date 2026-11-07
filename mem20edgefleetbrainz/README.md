# mem20edgefleetbrainz

**Edge Fleet Brain (RM-041).** Coordinate heterogeneous computers, phones,
servers and appliances as one capability-aware fleet.

The breakthrough this implements is concrete: **idle hardware becomes an
intelligent private compute cloud**. A rack server, a phone on a charger, a NAS
appliance and a laptop that wakes for two hours are not interchangeable
"capacity". They differ in what they can run, what they cost, how hot they run
and how likely they are to disappear mid-job. The fleet brain keeps those
differences explicit and answers one question continuously: *given this
workload, which reachable machine should run it, and why?*

This is not a scheduling demo. The subsystem has a real domain model, a durable
SQLite state plane, a running orchestration service, a JSON HTTP API with a
served operator cockpit, an estate-shell monitor, six live cross-subsystem
judgements, and 77 tests that assert on values the other subsystems compute.

## At a glance

| metric | value |
|---|---|
| package modules | `domain`, `store`, `ecosystem`, `service`, `runtime` |
| package lines | 2,654 |
| test files / tests | 6 / 77 |
| web assets | `web/index.html`, `web/style.css`, `web/app.js` |
| console entry point | `mem20edgefleetbrainz` |
| state plane | SQLite (WAL), versioned rows + append-only journals |
| cross-subsystem peers | 6, each called on the normal request path |
| conformance | 7/7 |

## Repository layout

```
mem20edgefleetbrainz/
  mem20edgefleetbrainz/
    domain.py      pure models, placement scoring, energy, fault forecasting
    store.py       SQLite state plane: nodes, workloads, placements, events, snapshots
    ecosystem.py   the six peer adapters (unique to this subsystem)
    service.py     submit -> place -> reserve -> dispatch -> complete/fail -> evacuate
    runtime.py     argparse CLI + ThreadingHTTPServer JSON API + static cockpit
    web/           served operator cockpit (vanilla JS, no build step)
  tests/           domain, store, service, http, ecosystem, runtime
  docs/PLAN.md     design and delivery record
  conftest.py      package-shadowing bootstrap for per-project pytest runs
  pyproject.toml   package, console script, web package-data, pytest config
```

## Mental model

```
                 submit                dispatch                    complete/fail
  client ──> workload queue ──> placement decision ──> running ──> completed / failed
                                     │  │
                                     │  └─ explains: components, alternatives,
                                     │     bottlenecks, confidence
                                     │
                     ┌───────────────┴────────────────┐
                     │  six live peer judgements      │
                     │  swarm · energy · device fit   │
                     │  hardware · roaming · sleep    │
                     └────────────────────────────────┘
                                     │
                        SQLite WAL state plane + event stream
```

A placement is never just "the node with the most free cores". Every feasible
node is scored on seven weighted factors, then adjusted by the peers' findings:

| factor | weight | what it measures |
|---|---|---|
| capability | gate | required capabilities are a hard prerequisite |
| cpu | 0.16 | free cores relative to capacity |
| memory | 0.12 | free memory relative to capacity |
| energy | 0.20 | marginal Wh against the workload's energy budget |
| cost | 0.12 | node price for the expected duration |
| reliability | 0.22 | node reliability minus its forecast fault risk |
| latency | 0.10 | link latency, including remote transport |
| locality | 0.08 | local region vs federated credit |

Cross-system bonuses can break a tie; they can never rescue an infeasible node.
The full decision — chosen node, score, components, alternatives, bottlenecks,
confidence — is written to an append-only journal, because "why did the
scheduler pick that node" is the question asked after an incident.

## Domain model (`domain.py`)

Pure functions and typed models. No I/O, no clock reads unless a caller passes
`now`, no imports from sibling subsystems.

- `DeviceKind`: `server`, `laptop`, `phone`, `appliance`, `edge_box`.
- `NodeStatus`: `online`, `draining`, `degraded`, `sleeping`, `offline`.
- `WorkloadState`: `queued`, `running`, `completed`, `failed`, `evicted`.
- `Node`: cores, memory, GPUs, bandwidth, idle/peak watts, price, reliability,
  latency, region, uptime, temperature, fault count, current load.
- `Workload`: required capabilities, CPU/memory, GPUs, priority, duration,
  deadline, price ceiling, energy budget, retry budget, locality requirement.
- Validation is real and happens before storage: `cpu_cores > 0`,
  `peak_watts >= idle_watts >= 0`, `0 <= reliability <= 1`, bounded priority,
  positive duration, non-negative retries.

**Energy** charges the marginal draw, not the peak nameplate: a 0.8-core job on
an idle 8-core box is `idle + (peak - idle) * 0.1`, and an already-warm node
starts from its current load instead of from zero.

**Fault risk** combines reliability, uptime, temperature, load, fault history
and heartbeat staleness, and scales with the forecast horizon. It returns a
recommendation (`healthy`, `watch`, `drain`, `evacuate`) and the drivers that
produced it, so the operator sees *why* a machine is considered risky.

**Fleet-wide plans** are pure too: `place_workload`, `rebalance_plan`,
`evacuation_plan`, `fleet_health`, `energy_profile`, `predict_fleet_faults`.
Evacuation reports stranded work instead of pretending a drain succeeded.

## State plane (`store.py`)

SQLite in WAL mode, because the fleet is written from the scheduler thread and
read from HTTP handlers at the same time, and because an edge box loses power:
a committed placement must survive a hard reset without a repair pass.

| shape | semantics |
|---|---|
| `nodes`, `workloads` | JSON payload + monotonic `version`; optimistic concurrency |
| `placements` | append-only decision journal with explanation and bottlenecks |
| `events` | ordered subscription stream (`seq`, `ts`, `kind`, `payload`) |
| `snapshots` | whole-fleet point-in-time copy for rollback |
| `idempotency` | retried submissions return the original workload |

`put_*`/`delete_*` accept an optional `expected_version` and raise
`ConflictError` on a race instead of silently winning it. Snapshots restore the
whole fleet and reset versions to the snapshot's state, so post-restore
concurrency checks stay honest.

## Lifecycle (`service.py`)

```
submit -> place -> reserve -> dispatch -> complete / fail -> retry | failed
                              │
                              ├─ drain -> evacuate (move or report stranded)
                              └─ rebalance (plan, optionally apply)
```

- **Submit** validates first, then stores; an `idempotency_key` replays the
  original workload instead of creating a duplicate.
- **Dispatch** applies the sleep policy, calls the six peers, scores every
  feasible candidate, reserves CPU/memory, marks the workload `running`, and
  records the decision. Unplaceable work stays `queued` with explicit
  bottlenecks.
- **Complete/fail** releases the reservation; a tolerated failure re-queues up
  to the bounded retry budget and increments the node's fault count.
- **Drain** marks a node `draining`. **Evacuate** moves every running workload
  to a scored alternative, then marks the source `offline`; if nothing fits,
  the stranded workloads are reported and the node stays `draining`.
- **Rebalance** moves work off nodes above a load threshold, optionally applying
  the plan and emitting a `fleet.rebalanced` event.
- **Sleep** is owned by the sleep subsystem: idle nodes may hibernate, a
  low-priority dispatch never sleeps the last awake node, and priority ≥ 60
  wakes hibernating nodes because paying the wake cost beats missing the
  deadline.

## Cross-subsystem wiring (`ecosystem.py`)

The fleet-specific peer set is deliberately *not* the common
memory/focus/catalog/webhook set. Each peer owns a distinct part of the
physical-device problem, and each adapter is called on the normal
register/submit/dispatch path.

| subsystem | functions actually called | what the fleet asks it |
|---|---|---|
| `mem20zerotouchnodeswarmz` | `register_node`, `discover`, `quorum`, `assign_task` | will the swarm admit this node, and is there quorum |
| `mem20energyawarecomputemigrationz` | `energy_cost`, `carbon_footprint`, `greenest_node`, `migrate_decision` | what does this placement cost in energy and carbon |
| `mem20devicecapabilitycompilerz` | `detect_capabilities`, `compatibility`, `feature_flags` | what tier is this device, and can it run the job |
| `mem20hardwaremarketplacez` | `price_estimate`, `search`, `marketplace_health` | what is this hardware worth, and what is on the market |
| `mem20roamingworkloadschedulerz` | `schedule`, `node_load`, `scheduler_health` | an independent load-only assignment to compare against |
| `mem20modelsleepandwakesystemz` | `track_activity`, `should_sleep`, `sleep`, `wake`, `sleep_health` | which idle nodes may hibernate, and which must wake |

Divergence is surfaced rather than hidden: when the fleet scorer and the
roaming scheduler disagree, both answers are in the report. A peer that is
missing or raises becomes `{"ok": false, "error": ...}` and never aborts a
schedule; the service reports the unavailable judgement so an operator can see
which part of the decision was blind.

`doctor()` probes all six and returns the reachable set. `simulate()` runs six
real scenarios end to end on a throwaway store: success, malformed input,
disconnection, overload, provider loss, restart recovery.

## CLI

Every command prints one JSON object; errors print JSON and exit 1.

```bash
python -m mem20edgefleetbrainz --store /tmp/fleet.db status
python -m mem20edgefleetbrainz --store /tmp/fleet.db metrics
python -m mem20edgefleetbrainz --store /tmp/fleet.db doctor
python -m mem20edgefleetbrainz --store /tmp/fleet.db simulate
python -m mem20edgefleetbrainz --store /tmp/fleet.db benchmark --iterations 20
python -m mem20edgefleetbrainz --store /tmp/fleet.db node add --id rack-a --kind server \
    --cpu 16 --memory 32 --gpus 1 --capabilities cpu,gpu --reliability 0.99 \
    --price 0.18 --region local
python -m mem20edgefleetbrainz --store /tmp/fleet.db node list
python -m mem20edgefleetbrainz --store /tmp/fleet.db node status rack-a draining
python -m mem20edgefleetbrainz --store /tmp/fleet.db node drain rack-a
python -m mem20edgefleetbrainz --store /tmp/fleet.db node evacuate rack-a
python -m mem20edgefleetbrainz --store /tmp/fleet.db node delete rack-a
python -m mem20edgefleetbrainz --store /tmp/fleet.db workload submit --id render \
    --name "nightly render" --cpu 6 --memory 8 --capabilities cpu,gpu \
    --priority 70 --duration 900 --deadline 3600 --idempotency-key demo-render
python -m mem20edgefleetbrainz --store /tmp/fleet.db workload list
python -m mem20edgefleetbrainz --store /tmp/fleet.db workload get render
python -m mem20edgefleetbrainz --store /tmp/fleet.db workload complete render \
    --reason "finished"
python -m mem20edgefleetbrainz --store /tmp/fleet.db dispatch --id render
python -m mem20edgefleetbrainz --store /tmp/fleet.db rebalance --threshold 0.85 --apply
python -m mem20edgefleetbrainz --store /tmp/fleet.db predict --horizon 7200
python -m mem20edgefleetbrainz --store /tmp/fleet.db energy --hours 12
python -m mem20edgefleetbrainz --store /tmp/fleet.db events --since 0 --limit 20
python -m mem20edgefleetbrainz --store /tmp/fleet.db snapshot --label before-move
python -m mem20edgefleetbrainz --store /tmp/fleet.db restore snap-...
python -m mem20edgefleetbrainz --store /tmp/fleet.db serve --host 127.0.0.1 --port 8771
```

`--json` accepts a full object or `@file.json` on `node add` and
`workload submit`, which is how a provisioner submits hardware it discovered
without translating every field onto flags. The store path defaults to
`$MEM20_EDGEFLEET_STORE` or `~/.mem20/edgefleet/fleet.db`.

## HTTP API

`serve` binds a `ThreadingHTTPServer` and prints its URL. The same process
serves the cockpit at `/` and the JSON API below. Validation maps to 400,
missing objects to 404, version races to 409, and an unhandled failure to 500
with the exception named. CORS is enabled so the static estate page can read it.

| method | path | purpose |
|---|---|---|
| GET | `/api/healthz` | availability, capacity and utilisation |
| GET | `/api/status` | health + metrics + energy + faults + sleep + roaming |
| GET | `/api/nodes` | node inventory |
| GET | `/api/workloads?state=running` | queue, optionally filtered |
| GET | `/api/workloads/{id}` | one workload |
| GET | `/api/events?since=0&limit=200` | ordered event stream |
| GET | `/api/metrics` | raw state-plane counts |
| GET | `/api/predict?horizon_s=3600` | fault forecast |
| GET | `/api/energy?hours=24` | projected energy draw |
| GET | `/api/doctor` | probe all six peers |
| GET | `/api/benchmark?iterations=20` | measure the placement path |
| POST | `/api/nodes` | register a node (201) |
| POST | `/api/workloads` | submit a workload (201) |
| POST | `/api/dispatch` | place queued work |
| POST | `/api/nodes/{id}/drain` | mark draining and plan evacuation |
| POST | `/api/nodes/{id}/evacuate` | move work and take the node offline |
| POST | `/api/nodes/{id}/status` | set `online`/`draining`/`degraded`/`sleeping`/`offline` |
| POST | `/api/workloads/{id}/complete` | complete or fail a workload |
| POST | `/api/rebalance` | plan (or apply) rebalance moves |
| POST | `/api/simulate` | run the six scenarios |
| POST | `/api/snapshot` / `/api/restore` | whole-fleet rollback |
| DELETE | `/api/nodes/{id}` / `/api/workloads/{id}` | delete |

## Runnable example

The block below is the real flow, run on this branch. It registers a GPU server
and a phone, submits a GPU workload, dispatches it, and reads the fleet status.

```bash
cd /opt/mem20
rm -rf /tmp/fleet-demo && mkdir -p /tmp/fleet-demo
PYTHONPATH=/opt/mem20/mem20edgefleetbrainz .venv/bin/python - <<'PY'
from mem20edgefleetbrainz.service import FleetService

svc = FleetService("/tmp/fleet-demo/fleet.db")
svc.register_node({"node_id": "rack-a", "kind": "server", "cpu_cores": 16,
                   "memory_gb": 32, "gpu_count": 1, "capabilities": ["cpu", "gpu"],
                   "reliability": 0.99, "price_per_hour": 0.18, "region": "local"})
svc.register_node({"node_id": "charge-phone", "kind": "phone", "cpu_cores": 4,
                   "memory_gb": 4, "capabilities": ["cpu"], "reliability": 0.86,
                   "price_per_hour": 0.0, "region": "local"})
submitted = svc.submit_workload({
    "workload_id": "render", "name": "nightly render", "cpu": 6, "memory_gb": 8,
    "required_capabilities": ["cpu", "gpu"], "priority": 70,
    "duration_s": 900, "deadline_s": 3600, "idempotency_key": "demo-render",
})
print("submitted:", submitted["created"], submitted["workload"]["state"])
print("compatible:", submitted["compatible_nodes"])
dispatched = svc.dispatch("render")["decisions"][0]
print("chosen:", dispatched["decision"]["chosen"],
      "score:", dispatched["decision"]["score"],
      "confidence:", dispatched["decision"]["confidence"])
print("bonuses:", dispatched["cross_system_bonuses"])
print("energy:", dispatched["energy"]["greenest"],
      dispatched["energy"]["energy_cost"], "cost,",
      dispatched["energy"]["carbon_g"], "g CO2")
health = svc.status()["health"]
print("health:", health["health"], "| util:", health["cpu_utilisation"],
      "| at risk:", health["at_risk"])
simulated = svc.simulate()
print("simulate:", simulated["passed"], "/", simulated["total"])
PY
```

Real output of the block above:

```
submitted: True queued
compatible: ['rack-a']
chosen: rack-a score: 0.946134 confidence: 0.968687
bonuses: {'rack-a': 0.06, 'charge-phone': 0.03}
energy: rack-a 1.8e-05 cost, 0.0406 g CO2
health: 0.91 | util: 0.3 | at risk: []
simulate: 6 / 6
```

The same lifecycle through the CLI:

```bash
S=/tmp/fleet-demo/fleet.db
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20edgefleetbrainz --store "$S" \
  node add --id rack-a --kind server --cpu 16 --memory 32 --gpus 1 \
  --capabilities cpu,gpu --reliability 0.99 --price 0.18 --region local
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20edgefleetbrainz --store "$S" \
  node add --id charge-phone --kind phone --cpu 4 --memory 4 \
  --capabilities cpu --reliability 0.86 --price 0 --region local
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20edgefleetbrainz --store "$S" \
  workload submit --id render --cpu 6 --memory 8 --capabilities cpu,gpu \
  --priority 70 --duration 900 --deadline 3600 --idempotency-key demo-render
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20edgefleetbrainz --store "$S" \
  dispatch --id render
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20edgefleetbrainz --store "$S" status
```

`dispatch` returns the full decision; trimmed here to the fields the cockpit
uses (the live response also carries the chosen node object and the complete
component breakdown):

```json
{
  "dispatched": 1,
  "decisions": [
    {
      "placed": true,
      "decision": {
        "chosen": "rack-a",
        "score": 0.946134,
        "confidence": 0.968687,
        "bottlenecks": [
          "charge-phone: missing capabilities gpu; cpu 4.0/6.0; memory 4.0/8.0GB",
          "only one feasible node; no failover candidate"
        ]
      },
      "cross_system_bonuses": {"charge-phone": 0.03, "rack-a": 0.06},
      "energy": {"greenest": "rack-a", "energy_cost": 0.000018, "carbon_g": 0.0406},
      "roaming": {"assignments": [{"workload": "render", "node": "charge-phone"}]},
      "sleep": {"sleeping": [], "awake": ["charge-phone", "rack-a"]},
      "woken": []
    }
  ]
}
```

Measured on this branch: `benchmark --iterations 20` over 12 synthetic nodes
returns **5,098 ops/sec** (p50 0.196 ms, p95 0.380 ms). That number is a
placement-path measurement on this machine, not a hardware-independent claim.

## Web surfaces

There are two, and they do not duplicate state:

1. **Operator cockpit** — served by the fleet process at `GET /` from `web/`.
   Register nodes, submit workloads, dispatch, drain/evacuate, watch energy,
   faults and the live event stream, run the simulator/doctor/rebalance.
2. **Estate monitor** — `docs/app/fleet/index.html` in the `docs/app` shell.
   A static page that reads the same JSON API (`?api=http://host:port`, stored
   in `localStorage`) and links to the cockpit. It owns no state, so the two
   views cannot drift apart.

## Tests

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20edgefleetbrainz -q
# 77 passed
```

| file | what it proves |
|---|---|
| `tests/test_domain.py` | real arithmetic: marginal energy, fault growth, hard gates, weighted scoring, rebalance/evacuation/health |
| `tests/test_store.py` | WAL durability, version conflicts, the decision journal, resumable events, snapshot rollback, idempotency |
| `tests/test_service.py` | full lifecycle, idempotent submission, bounded retries, sleep policy, drain/evacuate, rebalance, six-peer doctor |
| `tests/test_http.py` | a real `ThreadingHTTPServer` on an ephemeral port: static assets, CRUD, observability, snapshot/restore, 400/404/409 mapping, traversal refusal |
| `tests/test_ecosystem.py` | the values the six peers compute (swarm quorum, greenest node, device tier, market quote, roaming loads, sleep split) |
| `tests/test_runtime.py` | every CLI subcommand, `--json @file`, env/default store, error exit codes |

No mock replaces a subsystem boundary in the integration tests: the peers are
imported and called, and the HTTP suite uses a real socket.

## Conformance

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20edgefleetbrainz
```

The seven criteria: domain logic present, no stubs, tests collect, CLI surface,
README example, ≥5 cross-modules imported **and called on covered lines**, and
registration in the gateway registry (`gateway/mem20_gateway.py`, entry
`python -m mem20edgefleetbrainz status`).

## Design decisions and limits

- **Capabilities are a hard gate, not a soft score.** A phone cannot run a CUDA
  job, so a high score is never allowed to override a missing capability.
- **Price and energy ceilings reject rather than penalise.** A workload that
  cannot meet its budget stays queued with the reason, instead of silently
  running over budget.
- **The decision journal is append-only.** Rebalances and evacuations write new
  decisions; history is never rewritten.
- **The peers inform, they do not own.** A peer outage degrades the explanation
  and is reported as unavailable; the fleet keeps scheduling on its own model.
- **This is a single-fleet process.** The state plane is one SQLite database on
  one host. Multi-region federation is expressed through `region`,
  `remote_latency` and `federated_credit`, not through a distributed consensus
  layer. That keeps the failure model honest for an edge fleet that is expected
  to lose power and connectivity.

See [`docs/PLAN.md`](docs/PLAN.md) for the design and delivery record.
