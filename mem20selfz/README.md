# mem20selfz — Selfz

First-class mem20 subsystem/crew runtime for self-model integration with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core APIs preserved (`estate_context`, `MEMBERS`, `__version__`, legacy `--members/--version`).

## Peers (6)
`mem20episodicmemorygraphz`, `mem20rewardforgez`, `mem20causalroutingbrainz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20universalhealthnervoussystemz`.

## Python API (runnable)
```python
from mem20selfz.domain import self_report, probe, estate_context
r=self_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
print(estate_context()["peer_count"])  # 6
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfz --members
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfz serve --port 8828
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/selfz/index.html` (no Vite edits).

## MCP & registration
`SelfzToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20selfz/mem20selfz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20selfz
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

## Absorbed: `mem20episodicmemorygraphz`

# mem20episodicmemorygraphz — Episodic Memory Graph (RM-021, #306)

**Outcome:** store experiences as linked people, places, goals, actions, outcomes, and time.  
**Breakthrough:** memory becomes navigable experience rather than a pile of text chunks.

First-class implementation: legacy-compatible episode API plus graph navigation/query/timeline/entity indexing, durable SQLite WAL state, CLI + JSON HTTP API + cockpit, `docs/app` monitor, and 6 **unique** peer integrations (different from #300-#305).

## Legacy-compatible API
`create_episode(title,events=None)`, `add_event(ep,event)`, `link_episodes(episodes,a,b,relation='follows')`, `recall(episodes,query)`, `episode_graph(episodes)`, `forget(episodes,older_than)`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls | Contribution |
|---|---|---|
| `mem20dynamicskillgraphz` | `add_skill`,`update_proficiency`,`learning_path`,`skill_gap`,`graph_stats` | skill/proficiency graph over episode actions/outcomes |
| `mem20reversibleexecutiongraphz` | `create_graph`,`add_node`,`undo`,`redo`,`graph_health` | reversible episode/replay graph |
| `mem20mixedinitiativefocusenginez` | `focus_score`,`suggest`,`take_over`,`blend`,`focus_health` | focus/attention for recall lens |
| `mem20spatialcommanduniversez` | `create_region`,`add_entity`,`distance`,`in_region`,`spatial_health` | spatial/place indexing |
| `mem20crossproductloyaltygraphz` | `add_edge`,`degree`,`centrality`,`recommend_products`,`loyalty_score` | relationship centrality/recommendations |
| `mem20deterministicconfigurationgraphz` | `add_node`,`add_edge`,`resolve`,`validate`,`diff_configs` | deterministic relationship/config resolution |

## Runnable example (verified)

```bash
cd /opt/mem20
DB=/tmp/emg-demo.sqlite3
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20episodicmemorygraphz --db "$DB" create --title "ship fix"
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20episodicmemorygraphz --db "$DB" recall fix
```

Observed (key fields): `create` returns `ok=true`, episode id/title/events, and peer signals (`focus_recall`, `spatial_places` all `ok:true`). `recall` returns matching episodes and `focus_recall` signal.

```bash
python -m mem20episodicmemorygraphz status
python -m mem20episodicmemorygraphz doctor
python -m mem20episodicmemorygraphz simulate
python -m mem20episodicmemorygraphz serve --port 8786
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20episodicmemorygraphz/tests -q
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20episodicmemorygraphz
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

## Absorbed: `mem20universalhealthnervoussystemz`

# mem20universalhealthnervoussystemz — Universal Health Nervous System

First-class mem20 subsystem for universal health aggregation (register_subsystem/check_all/overall/health_report) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20faultcontainmentcellsz`, `mem20autonomousrecoverydirectorz`, `mem20selfhealingplansz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20universalhealthnervoussystemz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20universalhealthnervoussystemz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20universalhealthnervoussystemz serve --port 8842
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

## Absorbed: `mem20buildsequenceoptimizerz`

# RM-193 — Build Sequence Optimizer

**Owner:** Patricia  
**Lane:** Executable planning, dependency modeling, and build sequencing

## Outcome
Find faster and safer implementation orders under real resource constraints

## Breakthrough
Projects reduce idle time and avoid expensive rework

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-193 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20milestoneriskpredictorz`

# RM-197 — Milestone Risk Predictor

**Owner:** Patricia  
**Lane:** Executable planning, dependency modeling, and build sequencing

## Outcome
Forecast likely delay and failure points from dependency and runtime signals

## Breakthrough
Attention moves to the milestone before it becomes a crisis

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-197 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20qualityriskforecasterz`

# RM-174 — Quality Risk Forecaster

**Owner:** Mary  
**Lane:** Completion, review, quality, and user-outcome validation

## Outcome
Predict likely defects from change size, dependency shape, history, and runtime behavior

## Breakthrough
Testing effort targets the areas most likely to fail

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-174 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20quantuminspiredoptimizerz`

# RM-105 — Quantum-Inspired Optimizer

**Owner:** OtherStack  
**Lane:** Experimental and incompatible technology incubator

## Outcome
Apply annealing and tensor-inspired heuristics to hard scheduling and search problems

## Breakthrough
The platform explores solution spaces ordinary greedy algorithms miss

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-105 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20releasereadinesspredictorz`

# RM-179 — Release Readiness Predictor

**Owner:** Mary  
**Lane:** Completion, review, quality, and user-outcome validation

## Outcome
Forecast whether a candidate build can survive expected load, usage, and failure conditions

## Breakthrough
Release decisions become proactive instead of hopeful

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-179 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20selfhealingruntimecivilizationz`

# RM-217 — Self-Healing Runtime Civilization

**Outcome:** Coordinate prediction, diagnosis, repair, migration, and recovery across every runtime
**Breakthrough:** The ecosystem remains operational through failures that would stop ordinary platforms

A civilization here is a set of agents plus the dependency edges between them. An agent is usable
while its own health is unspent **and** the agents it depends on are usable — failure propagates
along the graph. One cycle is: **sample → quarantine → cascade → repair (bounded) → recover
(all-or-nothing)**.

Two invariants are the point of the design:

- **Bounded work.** A cycle performs at most one repair attempt per unhealthy agent, and an agent has
  a hard lifetime repair budget. A permanently dead dependency can never make the controller spin.
- **No silent recovery.** `status` reports `recovered` only when nothing is left unhealthy. A
  partially healed fleet reports `degraded` — it never rounds up.

## Install (source only — mem20 is not on PyPI)

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -r requirements.txt
```

There is no `pip install mem20`. The subsystem itself is standard-library-only; it reaches the rest
of mem20 through the repository tree, which is why it must run from a clone.

## Quickstart — run the demo cycle

```bash
cd mem20selfhealingruntimecivilizationz
python3 -m mem20selfhealingruntimecivilizationz demo
```

Real output (abridged to the decision-relevant fields):

```json
{
  "status": "healthy",
  "quarantined": ["gateway", "mcp", "memory_engine", "sdk"],
  "cascaded": ["mcp", "memory_engine", "sdk"],
  "repaired": ["gateway", "mcp", "memory_engine", "sdk"],
  "recovered": true,
  "remaining": [],
  "health": {"agents": 4, "alive": 4, "quarantined": 0, "dead": 0,
             "avg_health": 0.925, "usable_ratio": 1.0}
}
```

The gateway drops to 0.20 (below the 0.30 threshold); its dependents are quarantined by the cascade
and every agent is repaired inside the budget, so the cycle recovers in one pass.

## Run it against the real estate

```bash
cd mem20selfhealingruntimecivilizationz
python3 -m mem20selfhealingruntimecivilizationz probe              # which mem20 integrations resolve
python3 -m mem20selfhealingruntimecivilizationz --state-dir /tmp/sh run --cycles 2
python3 -m mem20selfhealingruntimecivilizationz report
python3 -m mem20selfhealingruntimecivilizationz serve --port 8099  # /health /ready /metrics
```

`probe` on this checkout reports **7/7** integrations:

```
available: 7 / 7
  MemoryEngineBridge     True memory
  RetrievalBridge        True retrieval_v2
  HealthSurfaceBridge    True mcp/health.py
  GatewayBridge          True mem20_gateway
  ToolchestBridge        True toolchest.catalog
  KilnBudgetBridge       True mem20kilnz.budgets
  PlansEngineBridge      True mem20selfhealingplansz
```

`run --cycles 2` builds the fleet from the real catalogue and repairs it:

```
cycle 1 | status healthy | quarantined 12 | repaired 12 | budget 3 | ts_validated True
cycle 2 | status healthy | quarantined 0  | repaired 0  | budget 3 | ts_validated True
```

Subsystems that are importable start near-full health, ones that are not start degraded, so the first
cycle has genuine work to do instead of a synthetic scenario.

## Library

```python
from mem20selfhealingruntimecivilizationz import Civilization, FleetController

civ = Civilization(threshold=0.3, repair_amount=0.5, max_repairs=3)
civ.add_agent("gateway")
civ.add_agent("mcp", depends_on=["gateway"])
civ.damage("gateway", 0.8)
record = civ.run_cycle()          # bounded; returns what happened
assert civ.status() == "healthy"  # recovered in one pass

controller = FleetController.from_catalogue(limit=6)
controller.cycle()
controller.metrics_snapshot()
```

## Substrate: what this subsystem actually uses (criterion 6)

Seven mem20 modules are imported **and called on a tested path** — see
`mem20selfhealingruntimecivilizationz/integrations.py` and
`tests/test_integration.py`:

| Module | What it actually does here |
|---|---|
| `memory_engine.memory` | `validate_event_time` stamps every cycle record; `redact_secrets` scrubs repair error text before persist/publish |
| `memory_engine.retrieval_v2` | `decompose_query` splits a failure description into repair targets |
| `mcp/health.py` | the shared `/health /ready /metrics` server, fed by a live adapter over this controller |
| `gateway.mem20_gateway` | `register_agent` announces the subsystem; `broadcast` publishes each cycle summary |
| `toolchest.catalog` | `discover_subsystems` is the fleet roster and the importability signal |
| `mem20kilnz` | `TRIANGLE_BUDGETS` is the source of the per-subsystem repair ceiling |
| `mem20selfhealingplansz` | `Engine.execute` decides the repair action (failover/restart) instead of a local rule |

## Tool surface (criterion 7)

Three MCP tools live in `mcp/tools/civilization_tools.py`, following the same
`*ToolsMixin` shape as `braid_tools.py`:

| Tool | What it does |
|---|---|
| `civilization_health` | fleet status, per-agent health, budget, resolved integrations |
| `civilization_cycle` | run 1–5 bounded cycles over the real catalogue and persist the records |
| `civilization_report` | full report: civilization state, planner actions, budget, metrics |

They are callable and tested today — the test imports the module exactly the way the server
does and calls every tool:

```bash
# from the repository root
python3 -c "import sys; sys.path.insert(0, 'mcp'); \
from tools.civilization_tools import CIVILIZATION_TOOLS, tool_specs; \
print(sorted(tool_specs())); \
print(CIVILIZATION_TOOLS['civilization_health'](None)['status'])"
```

Real output:

```
['civilization_cycle', 'civilization_health', 'civilization_report']
healthy
```

`mcp/server.py` composes its mixins from a hard-coded list and has no plugin/auto-discovery
hook, so serving these three tools also needs `CivilizationToolsMixin` added to
`Mem20MCPServer`'s bases — a one-line change in a 48 KB file that four other in-flight
branches also edit. That edit is deliberately **not** bundled here (it would conflict); it is
recorded as a follow-up in `docs/renovation/4.0/FINDINGS.md`. Until it lands the tools are
importable, tested and callable, but not yet served by the running server.

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `MEM20_SELFHEALING_STATE` | `state/selfhealing` | state dir (SQLite WAL store, gateway spool, planner DB) |

`ControllerConfig(threshold=0.30, repair_amount=0.50, max_repairs=3, history_limit=200, announce=True)`
overrides the same knobs from code.

## Tests

```bash
python3 -m pytest mem20selfhealingruntimecivilizationz -q
```

Contract, unit, property-based (Hypothesis with a deterministic fallback grid) and integration tests,
including a real HTTP request to the health surface and real gateway state files on disk.

## Named limits (not claimed complete)

Live product surfaces, real provider credentials, production traffic, and governed FreeStack
deployment remain target-environment integration. The planner is asked for an action and its
vocabulary drives the recovery amount; it does not execute the failover itself.

## Absorbed: `mem20selfrepairingtestfactoryz`

# RM-123 — Self-Repairing Test Factory

**Owner:** Judy  
**Lane:** Software engineering intelligence and repair

## Outcome
Generate, mutate, and maintain tests as application behavior evolves

## Breakthrough
Test coverage becomes a living system rather than a decaying asset

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-123 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.
