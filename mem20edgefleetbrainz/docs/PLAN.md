# mem20edgefleetbrainz — design and delivery record

Roadmap: **RM-041**, lane *Provider, device, research, and remote-compute fleet
control*. Outcome: coordinate heterogeneous computers, phones, servers and
appliances as one capability-aware fleet. Breakthrough: idle hardware becomes an
intelligent private compute cloud.

This document records why the subsystem is shaped the way it is, so a later
change can be judged against the original constraints instead of only against
the current code.

---

## 1. Why this is not a conformance shim

The first pass at the 4.0 conformance criteria produced shallow fixes across
many subsystems: a fenced README block, one smoke test, a gateway row and a
generic `estate_context()` probe. That pattern passes the mechanical gate without
making the subsystem real — nothing schedules, nothing persists, and no other
system ever sees a result.

This delivery replaces that for RM-041 with a depth-first implementation:

- a typed domain model with real physics and a real decision procedure;
- a durable SQLite state plane with versions, journals, events and snapshots;
- a service that runs the whole lifecycle and is the only writer;
- six peer subsystems actually called on the request path;
- a CLI, a JSON HTTP API, a served cockpit and an estate-shell monitor;
- tests that assert on computed values rather than import statements.

The subsystem is usable without any other mem20 process, and the peers enrich
the decision instead of being required for it.

## 2. Architecture

```
domain.py     pure: models, validation, scoring, energy, faults, plans
store.py      SQLite WAL: nodes, workloads, placements, events, snapshots, keys
ecosystem.py  six adapters; one peer per physical concern
service.py    orchestration + the only writer of the state plane
runtime.py    argparse CLI, ThreadingHTTPServer, static cockpit
web/          served operator cockpit
tests/        domain, store, service, http, ecosystem, runtime
```

The dependency direction is one-way: `runtime -> service -> {domain, store,
ecosystem}`. `domain` imports nothing from the package; `ecosystem` imports the
peers; `service` composes all three. That keeps the models testable without a
database or a sibling subsystem.

### 2.1 Domain decisions

- **Capabilities are a hard gate.** A phone cannot run a CUDA job. A soft
  penalty would let a high score mask an impossible placement, which is exactly
  the failure an operator cannot debug from the outside.
- **Energy is marginal, not nameplate.** Charging a workload the full peak draw
  makes an already-warm node look expensive and an idle node look free. The
  model charges `idle + (peak - idle) * resulting_load`, starting from the
  node's current load.
- **Reliability decays with uptime, heat, load, faults and heartbeat age.** A
  node that has been up for a month at 90 °C is a worse bet than a cold spare
  even when both report `online`. The forecast returns drivers so the
  recommendation (`healthy`, `watch`, `drain`, `evacuate`) can be explained.
- **Price and energy ceilings reject.** Exceeding a budget is not a penalty in a
  weighted sum; the workload stays queued and the bottleneck says why.
- **Ties are deterministic.** When no cross-system bonus distinguishes two
  candidates, the higher score wins and the node id breaks the remaining tie, so
  the same fleet and workload produce the same decision on every replay.
- **Plans are pure data.** `rebalance_plan` and `evacuation_plan` return moves
  and stranded work; the service decides whether to apply them. Evacuation
  never reports success while work is still stranded.

### 2.2 State-plane decisions

- **SQLite with WAL.** The scheduler thread writes while HTTP handlers read, and
  an edge box can lose power. WAL gives readers a consistent view without
  blocking the writer, and a committed placement survives a hard reset without a
  repair pass.
- **Versioned rows.** `nodes` and `workloads` carry a monotonic version.
  Mutations accept an optional `expected_version`; a mismatch raises
  `ConflictError` rather than silently overwriting a concurrent writer.
- **Append-only placement journal.** "Why did the scheduler pick that node" is
  asked after an incident. The decision, its components, alternatives and
  bottlenecks are written once and never rewritten.
- **Events are ordered and resumable.** The HTTP surface polls `since=<seq>`;
  the sequence is the cursor. A slow consumer catches up instead of missing
  events.
- **Snapshots are whole-fleet rollback.** Restore replaces nodes, workloads and
  their versions, so post-restore concurrency checks stay meaningful. Restore is
  itself an event.
- **Idempotency lives in its own table.** A retried submission returns the
  original workload; the state plane, not the client, owns that promise.

### 2.3 Ecosystem decisions

The peer set was chosen to cover the physical problem, not to reuse a standard
template. **Wiring rule (applies to every subsystem fixed depth-first): the ≥5
cross-module peers must be a different set on each subsystem, chosen for that
subsystem's job — never the same memory/focus/catalog/webhook template copied
across issues.** Each peer below owns something the fleet cannot compute about
itself:

| peer | why the fleet needs it |
|---|---|
| `mem20zerotouchnodeswarmz` | membership and quorum: whether the swarm would accept the node at all |
| `mem20energyawarecomputemigrationz` | energy and carbon cost, and whether a migration is worth it |
| `mem20devicecapabilitycompilerz` | device tier, ML/3D fitness, feature flags from hardware |
| `mem20hardwaremarketplacez` | what the hardware is worth and what is on the market |
| `mem20roamingworkloadschedulerz` | an independent load-only assignment to compare against |
| `mem20modelsleepandwakesystemz` | idle policy: which nodes may sleep and which must wake |

The adapters translate between vocabularies (`node_id`/`id`, `cpu`/`cost`,
`peak_watts`/`power_watts`) at the seam. They never leak a peer's data shape
into the service. A peer failure is recorded as `{"ok": false, "error": ...}`
and reported; scheduling continues on the fleet's own model, and `doctor()`
names the unavailable judgement.

Divergence is a feature: the roaming scheduler is load-only, the fleet scorer is
energy- and reliability-aware. When the two disagree the report carries both,
and the operator sees that the decision is contested.

### 2.4 Runtime decisions

- **One implementation, two entries.** The CLI and HTTP server both call
  `FleetService`. A placement from a terminal is the same placement from the
  cockpit.
- **Real status codes.** Validation is 400, missing objects 404, version races
  409, unhandled failures 500 with the exception named. Static serving refuses
  path traversal before reading a file.
- **The served cockpit is the operator plane.** It registers nodes, submits
  work, dispatches, drains/evacuates, and shows energy, faults, events and the
  simulator. No build step, so the served assets are the source.
- **The estate monitor is read-only.** `docs/app/fleet/index.html` reads the same
  JSON API and owns no state, so the two surfaces cannot drift apart.

### 2.5 Sleep policy

The sleep decision belongs to `mem20modelsleepandwakesystemz`; the fleet applies
it with two guardrails that prevent starvation:

- low-priority work may sleep idle nodes but never the last awake node, so a
  queued workload can still be placed;
- priority 60 or above wakes every hibernating node, because paying the wake
  cost is cheaper than missing the deadline.

The node keeps its old `last_seen` while asleep, which makes the idle judgement
idempotent until an explicit wake updates the activity timestamp.

## 3. Delivery record

| step | result |
|---|---|
| domain rewrite | typed models, capability gate, marginal energy, fault forecasting, weighted scoring, rebalance/evacuation/health |
| persistence | WAL schema, versioned rows, placement journal, resumable events, snapshots, idempotency, metrics |
| ecosystem seam | six fleet-specific peers, real calls on register/submit/dispatch/rebalance |
| service | submit, dispatch, complete/fail with bounded retries, drain, evacuate, rebalance, sleep policy, simulate, benchmark, doctor |
| runtime | CLI subcommands, JSON API, status mapping, static cockpit, CORS for the estate page |
| frontend | served cockpit plus `docs/app/fleet/` monitor linked from `docs/app/README.md` |
| registration | `gateway/mem20_gateway.py` entry `python -m mem20edgefleetbrainz status` |
| tests | 77 across six files |
| conformance | 7/7 |

Bugs found by smoke testing and fixed during delivery:

- `rebalance` treated a `Workload` as a dict and passed a `Node` where the
  energy adapter expected a mapping;
- `simulate` used the wrong capability key and did not actually dispatch a
  workload before asserting disconnection;
- domain `ValueError`s escaped as 500 instead of 400 for node/workload/status
  validation;
- the sleep policy could hibernate the last awake node;
- `mem20energyawarecomputemigrationz.greenest_node` raised `TypeError` when two
  identical machines had equal cost, because `list.sort()` compared the node
  mappings as a tie-breaker; it now breaks ties by node id.

## 4. Verification

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20edgefleetbrainz -q
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20edgefleetbrainz \
  --store /tmp/fleet.db simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20edgefleetbrainz \
  --store /tmp/fleet.db doctor
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py \
  mem20edgefleetbrainz
```

Observed on this branch:

- 77 tests pass under the estate pytest configuration;
- `simulate` passes 6/6 scenarios (success, malformed, disconnection, overload,
  provider loss, restart recovery);
- `doctor` reaches all six peers;
- `benchmark --iterations 20` over 12 nodes: 5,098 ops/sec, p50 0.196 ms,
  p95 0.380 ms (machine-specific);
- conformance reports all seven criteria satisfied.

## 5. Limits and deliberate non-goals

- **Single-host state plane.** One SQLite database per fleet process. Federation
  is expressed as `region`, `remote_latency` and `federated_credit`; there is no
  distributed consensus layer pretending an edge fleet never partitions.
- **Energy model is analytical.** It projects from idle/peak watts and price. It
  does not read smart-plug telemetry; a caller that has telemetry can feed it
  through node fields.
- **No preemption.** A running workload is moved by drain/evacuate/rebalance,
  not by a priority preemption scheduler. Preemption needs a checkpoint contract
  the estate does not have yet.
- **Peer bonuses are bounded.** Bonuses adjust a score; they cannot make an
  infeasible node feasible. This is intentional so a peer outage cannot silently
  change what is placeable.
