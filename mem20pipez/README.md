# mem20pipez — unified pipeline system

Consolidated from all pipe subsystems. Aggregates pipeline runtimes and logic under one unified interface.

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

## Absorbed: `mem20autonomousmicrosaasfoundryz`

# mem20autonomousmicrosaasfoundryz — Autonomous Micro-SaaS Foundry

First-class mem20 subsystem for micro-SaaS founding: score ideas, generate MVP specs, plan launches, project revenue, and rank ideas — with **6 subsystem-specific estate peers** (no generic template), SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app integration, and real MCP tools.

## Architecture
- `domain.py` — pure ops + `foundry_report()`/`probe()`/`estate_context()`
- `ecosystem.py` — 6 adapters (bootstrap); failures reported, never fatal
- `runtime.py` — `Service` + SQLite WAL `EventStore`; CLI; HTTP API; serves `web/`
- `web/` — vanilla cockpit (no build). `docs/PLAN.md`, `docs/app/` monitor, gateway, MCP.

## Peers (6, subsystem-specific)
| peer | real functions | role |
|---|---|---|
| `mem20simz` | `revenue,profit,margin,scenario_sim` | economics/margin/scenarios |
| `mem20causalroutingbrainz` | `DemandForecastAndCapacityBrain` | demand forecast signal |
| `mem20studioz` | `schedule_projects,resource_allocation,studio_health` | MVP build scheduling |
| `mem20autonomoussaleslaboratoryz` | `pipeline_value,conversion_probability,segment_leads` | launch pipeline/leads |
| `mem20loreragcontentgeneratorz` | `generate,rank_adapters,quality_score` | landing/content quality |
| `mem20capabilitymarketplacez` | `CapabilityMarketplace` add/locate/distribution | capability/stack routing |

## Python API
```python
from mem20autonomousmicrosaasfoundryz.domain import (
    score_idea, mvp_spec, launch_plan, revenue_projection, idea_ranking,
    foundry_report, probe, estate_context,
)

idea = {"name": "tool", "market_size": 800, "competition": 2, "effort": 3, "features": ["auth","core","billing"], "price": 9}
print(score_idea(idea))
print(mvp_spec(idea))
print(launch_plan(idea))
print(revenue_projection(users=100, price=9))
print(idea_ranking([idea, {**idea, "market_size": 100}]))

report = foundry_report(idea)
print(report["ok"], report["idea_score"], len(report["peers"]))  # 6 peers
print(probe()["ok"])
print(estate_context()["peer_count"])
```

## CLI
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousmicrosaasfoundryz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousmicrosaasfoundryz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousmicrosaasfoundryz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousmicrosaasfoundryz simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousmicrosaasfoundryz serve --port 8783
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `POST /api/score`, `GET /api/events|health`. Cockpit at `/` (served). State: `~/.mem20/autonomousmicrosaasfoundryz/state.sqlite3` (SQLite WAL). docs/app: `docs/app/autonomousmicrosaasfoundryz/index.html` (no Vite assets edited), linked from `docs/app/README.md`.

```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousmicrosaasfoundryz serve --port 8783
```

## MCP & registration
`AutonomousMicroSaaSFoundryToolsMixin` (`mcp/tools/mem20autonomousmicrosaasfoundryz_tools.py`) in `mcp/server.py` (`autonomousmicrosaasfoundryz_status|doctor`). Gateway `SUBSYSTEMS` entry.

## Tests & conformance
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20autonomousmicrosaasfoundryz/mem20autonomousmicrosaasfoundryz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20autonomousmicrosaasfoundryz
node --check mem20autonomousmicrosaasfoundryz/mem20autonomousmicrosaasfoundryz/web/app.js
```
Target: **7/7**.

## Limits
Deterministic scoring/planning logic; real market/payment/hosting integrations are target-environment concerns. Peer unavailability surfaced, not fatal.

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

## Absorbed: `mem20datalocalityoptimizerz`

# mem20datalocalityoptimizerz — Data Locality Optimizer

First-class mem20 subsystem for data locality optimization (placement scoring, optimal placement, migration cost, locality reporting, rebalance) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20zerotouchnodeswarmz`, `mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20universalhealthnervoussystemz`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## Python API (runnable)
```python
from mem20datalocalityoptimizerz.domain import placement_score, optimal_placement, migration_cost, locality_report, rebalance, placement_report, probe
nodes=[{"id":"n1","latency_ms":1,"capacity_gb":10,"used_gb":0},{"id":"n2","latency_ms":20,"capacity_gb":10,"used_gb":0}]
print(optimal_placement({"size_gb":1}, [dict(n) for n in nodes])["id"])  # n1
print(migration_cost({"size_gb":10},{"egress_cost":0.1},{})==1.0)  # True
print(locality_report([{"local":True},{"local":False}])["ratio"])  # 0.5
r=placement_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20datalocalityoptimizerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20datalocalityoptimizerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20datalocalityoptimizerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20datalocalityoptimizerz serve --port 8799
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/datalocalityoptimizerz/index.html` (no Vite edits).

## MCP & registration
`DataLocalityOptimizerToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20datalocalityoptimizerz/mem20datalocalityoptimizerz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20datalocalityoptimizerz
```
Target **7/7**.

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

## Absorbed: `mem20goapagentdesignerz`

# mem20goapagentdesignerz — GOAP Agent Designer (RM-226, #320)

**Outcome:** build goal-oriented agents through a visual editor for actions, costs, perceptions, and memory.

Preserves legacy domain API and CAPABILITY Engine/CLI/10-scenario simulator. `search` is meaningful for GOAP design payloads and backward-compatible for generic search.

## Legacy domain API (preserved)
`plan(actions,start_state,goal_state)`, `action_cost(action)`, `heuristic(state,goal)`, `validate_plan(plan,actions)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | GOAP design role |
|---|---|---|
| `mem20simz` | `fairness_score`,`simulate_incentives` | incentive alignment for actions/agents |
| `mem20styleguideagentz` | `style_health`,`style_score` | design/spec quality checks |
| `mem20humanagentcoworkcanvasz` | `create_canvas`,`add_item`,`canvas_summary` | human-agent design collaboration |
| `mem20dynamicphasereplannerz` | `DynamicPhaseReplanner` (+ phase/order) | phase replanning structure |
| `mem20compoundingproductecosystemz` | `ecosystem_health`,`network_value`,`synergy` | agent ecosystem value signals |
| `mem20asynccollaborationcapsulesz` | `create_capsule`,`capsule_checksum`,`active_members` | async collaboration capsule |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20goapagentdesignerz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20goapagentdesignerz execute '{"actions":[{"name":"move","effects":{"at":"target"},"cost":1}],"start_state":{"at":"start"},"goal_state":{"at":"target"}}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20goapagentdesignerz serve --port 8800
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20goapagentdesignerz/tests mem20goapagentdesignerz/mem20goapagentdesignerz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20goapagentdesignerz
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

## Absorbed: `mem20realitytosoftwarecompilerz`

# mem20realitytosoftwarecompilerz — Reality-to-Software Compiler

First-class mem20 subsystem for compiling real-world specs to software (ingest, compile, validate, diff, health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20autonomoussoftwarefoundryz`, `mem20deterministicconfigurationgraphz`, `mem20eventstreamsuperhighwayz`, `mem20causalroutingbrainz`, `mem20faultcontainmentcellsz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20realitytosoftwarecompilerz.domain import ingest, compile_to_code, validate_spec, diff_spec, compiler_report, probe
s=ingest("name: demo"); print(s["name"])  # demo
print("Demo" in compile_to_code({"name":"demo"}))  # True
print(validate_spec({"name":"x"})["valid"])  # True
r=compiler_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realitytosoftwarecompilerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realitytosoftwarecompilerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realitytosoftwarecompilerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realitytosoftwarecompilerz serve --port 8810
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/realitytosoftwarecompilerz/index.html` (no Vite edits).

## MCP & registration
`RealityToSoftwareCompilerToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20realitytosoftwarecompilerz/mem20realitytosoftwarecompilerz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20realitytosoftwarecompilerz
```
Target **7/7**.

## Absorbed: `mem20selfoptimizingkernelz`

# mem20selfoptimizingkernelz — Self-Optimizing Kernel

First-class mem20 subsystem for self-optimizing kernels (parameter optimization, scoring, search) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20causalroutingbrainz`, `mem20causalroutingbrainz`, `mem20simz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20faultcontainmentcellsz`.

## Python API (runnable)
```python
from mem20selfoptimizingkernelz.domain import optimize, score, search, kernel_report, probe
print(optimize({"a":0},{"a":10},0.5)["a"])  # 5.0
print(score({"a":2},{"a":3}))  # 6
r=kernel_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfoptimizingkernelz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfoptimizingkernelz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfoptimizingkernelz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20selfoptimizingkernelz serve --port 8826
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/selfoptimizingkernelz/index.html` (no Vite edits).

## MCP & registration
`SelfOptimizingKernelToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20selfoptimizingkernelz/mem20selfoptimizingkernelz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20selfoptimizingkernelz
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

## Absorbed: `mem20universaldatatranslatorz`

# RM-162 — Universal Data Translator

**Owner:** Kimberly  
**Lane:** Schema, data shape, database, and information transformation

## Outcome
Map records, events, documents, and objects between incompatible systems

## Breakthrough
Any runtime can understand any other runtime through generated mappings

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-162 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.
