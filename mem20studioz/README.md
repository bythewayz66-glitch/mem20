# mem20studioz — Studioz (Studio Runtime)

Unified studio subsystem consolidating all studio/build/production runtimes under `mem20studioz/studios/`. First-class mem20 crew runtime for studio pipelines with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core APIs preserved (`estate_context` superset, `MEMBERS`/`__version__`, legacy `--members/--version`).

## Peers (6)
`mem20pipez`, `mem20pipez`, `mem20pipez`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20autonomousworkcellsz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20studioz --members
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20studioz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20studioz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20studioz serve --port 8837
```

## Absorbed: `mem20autonomousworkcellsz`

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
