# mem20facez — Interface & Workspace Crew Runtime (#312)

First-class interface/workspace runtime for 8 reviewed member systems. Preserves compatibility (`MEMBERS`, `__version__`, `mem20facez.cli:main`, `--version`, `--members`) and adds real member probing, composition planning, 6 unique cross-subsystem peer integrations, JSON CLI, HTTP API, and a static cockpit.

## Members (8, preserved)
`mem20adaptiveinterfacecomposerz`, `mem20musicvisualsynchronizerz`, `mem20parallelworkstreamcomposerz`, `mem20spatialcommanduniversez`, `mem20spatialexperiencedesignerz`, `mem20visualagentblackboardz`, `mem20visualdataflowcomposerz`, `mem20voicetoactionswitchboardz`.

## Unique cross-subsystem wiring (criterion 6)
| Peer | Real calls | Contribution |
|---|---|---|
| `mem20multimodaltaskcapturez` | `capture`,`merge_captures`,`extract_action_items`,`capture_health` | multimodal task capture |
| `mem20visualdataflowcomposerz` | `create_pipeline`,`add_node`,`connect` | visual dataflow composition |
| `mem20intenttomissioncompilerz` | `compile_mission`,`validate_mission`,`mission_progress` | intent→mission compilation |
| `mem20personalautomationcanvasz` | `create_canvas`,`add_workflow`,`add_trigger` | workspace automation canvas |
| `mem20multiworldsandboxz` | `create_world`,`branch`,`step` | sandboxed layout/world branching |
| `mem20visualagentblackboardz` | `create_blackboard`,`post`,`read` | visual agent coordination board |

## Runnable example (verified)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20facez --version
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20facez --members
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20facez doctor
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20facez compose --intent "visual workspace" --payload '{"mode":"visual"}'
```

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20facez serve --port 8792
```

HTTP: `/health`, `/status`, `/doctor`, `/compose` (POST), cockpit at `/`.

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20facez/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20facez
```

## Absorbed: `mem20intenttomissioncompilerz`

# RM-031 — Intent-to-Mission Compiler

Outcome: Convert a human objective into executable missions, dependencies, roles, and completion criteria

Breakthrough: A vague goal becomes a live operating plan in seconds

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `compose` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20intenttomissioncompilerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20intenttomissioncompilerz benchmark
```

## Absorbed: `mem20multimodaltaskcapturez`

# RM-037 — Multimodal Task Capture (#338)

**Outcome:** Turn speech, sketches, screenshots, gestures, and rough notes into structured executable work.  
**Operation kind:** `ingest`.

## 1st-class implementation
- **Domain:** `capture/merge_captures/extract_action_items/capture_health` (legacy) plus `ingest_capture` producing structured executable task + action items across modalities.
- **Runtime:** `ingest` wired to domain + 6 peer signals.
- **Ecosystem (6 peers, unique set):** `mem20modalitybridgez`, `mem20sensorymemoryingestz`, `mem20intentcompilerz`, `mem20twinz`, `mem20agentoutputcompilerz`, `mem20episodicmemorygraphz`.

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20multimodaltaskcapturez execute '{"text":"build api. test api","source":"chat"}'
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20multimodaltaskcapturez/mem20multimodaltaskcapturez/tests/test_domain.py -q
```
Gateway `SUBSYSTEMS["mem20multimodaltaskcapturez"]`; docs `docs/app/multimodaltaskcapturez/index.html`; target 7/7.

## Absorbed: `mem20multiworldsandboxz`

# RM-057 — Multi-World Sandbox

Outcome: Run the same plan against simulated environments, providers, and failure conditions

Breakthrough: Actions are rehearsed before touching real systems

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `simulate` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20multiworldsandboxz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20multiworldsandboxz benchmark
```

## Absorbed: `mem20musicvisualsynchronizerz`

# RM-138 — Music-Visual Synchronizer

**Owner:** Jammee  
**Lane:** Creative production, media, brand, and experience design

## Outcome
Generate and align motion, lighting, UI, and effects to live audio structure

## Breakthrough
Any experience can gain responsive audiovisual choreography

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-138 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20parallelworkstreamcomposerz`

# RM-196 — Parallel Workstream Composer

**Owner:** Patricia  
**Lane:** Executable planning, dependency modeling, and build sequencing

## Outcome
Split features into independent streams with precise merge points

## Breakthrough
Human and agent teams can build in parallel without collision

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-196 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20personalautomationcanvasz`

# mem20personalautomationcanvasz — Personal Automation Canvas

First-class mem20 subsystem for personal automation canvas (create_canvas/add_workflow/add_trigger/run_workflow/canvas_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20autonomousworkcellsz`, `mem20agentoutputcompilerz`, `mem20selfhealingplansz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20personalautomationcanvasz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20personalautomationcanvasz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20personalautomationcanvasz serve --port 8851
```

## Absorbed: `mem20spatialcommanduniversez`

# mem20spatialcommanduniversez — Spatial Command Universe

First-class mem20 subsystem for spatial command (create_region/add_entity/distance/in_region/spatial_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20autonomousworkcellsz`, `mem20causalroutingbrainz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20faultcontainmentcellsz`, `mem20universalhealthnervoussystemz`.

## Python API (runnable)
```python
from mem20spatialcommanduniversez.domain import create_region, add_entity, distance, spatial_report, probe
r=create_region("r1",[(0,10),(0,10)]); add_entity(r,"e1",(5,5)); print(distance((0,0),(3,4)))  # 5.0
rep=spatial_report(); print(rep["ok"], len(rep["peers"]))  # True 6
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20spatialcommanduniversez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20spatialcommanduniversez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20spatialcommanduniversez serve --port 8834
```

## Absorbed: `mem20spatialexperiencedesignerz`

# RM-137 — Spatial Experience Designer

**Owner:** Jammee  
**Lane:** Creative production, media, brand, and experience design

## Outcome
Compose immersive rooms, exhibits, stores, and game spaces from reusable primitives

## Breakthrough
3D experiences become accessible to ordinary product teams

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-137 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20visualagentblackboardz`

# mem20visualagentblackboardz — Visual Agent Blackboard

First-class mem20 subsystem for visual agent blackboard (create_blackboard/post/read/clear/blackboard_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20autonomousworkcellsz`, `mem20agentoutputcompilerz`, `mem20realtimeteampresencez`, `mem20episodicmemorygraphz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20visualagentblackboardz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20visualagentblackboardz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20visualagentblackboardz serve --port 8844
```

## Absorbed: `mem20visualdataflowcomposerz`

# mem20visualdataflowcomposerz — Visual Dataflow Composer

First-class mem20 subsystem for visual dataflow composition (create_pipeline/add_node/connect/execute/pipeline_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20visualagentblackboardz`, `mem20autonomousworkcellsz`, `mem20agentoutputcompilerz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20causalroutingbrainz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20visualdataflowcomposerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20visualdataflowcomposerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20visualdataflowcomposerz serve --port 8845
```

## Absorbed: `mem20voicetoactionswitchboardz`

# RM-117 — Voice-to-Action Switchboard

**Owner:** Sherry  
**Lane:** Human communication, presence, and relationship intelligence

## Outcome
Convert spoken requests into routed tasks, calls, device actions, and agent missions

## Breakthrough
Voice becomes a universal command layer for FreeStack

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-117 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

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

## Absorbed: `mem20goaleconomyschedulerz`

# mem20goaleconomyschedulerz — Goal Economy Scheduler (RM-056, #319)

**Outcome:** allocate scarce compute, money, time, and attention among competing goals.  
**Breakthrough:** resources flow toward the highest-value achievable outcomes.

Preserves legacy domain API and CAPABILITY Engine/CLI/10-scenario simulator. `schedule` is meaningful for goal-economy payloads and backward-compatible for generic node placement.

## Legacy domain API (preserved)
`schedule_goals(goals,budget)`, `goal_value(goal)`, `rebalance(goals,new_budget)`, `progress(goals,completed_ids)`, `priority_queue(goals)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Scheduling role |
|---|---|---|
| `mem20selfhealingplansz` | `create_plan`,`plan_status`,`heal_plan` | plan resilience/health |
| `mem20opportunityradarz` | `score_opportunity`,`rank`,`scan` | opportunity/value prioritization |
| `mem20revenueleakhunterz` | `detect_leaks`,`recoverable`,`hunter_health` | budget/money leak risk |
| `mem20milestoneriskpredictorz` | `MilestoneRiskPredictor.add_point/velocity/forecast` | milestone schedule forecast |
| `mem20humancapabilitysuperplatformz` | `capability_matrix`,`team_capability` | attention/execution capacity |
| `mem20facez` | `compose_plan`,`probe_members` | control interface composition |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20goaleconomyschedulerz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20goaleconomyschedulerz execute '{"goals":[{"id":"g1","value":10,"cost":3},{"id":"g2","value":8,"cost":2}],"budget":4}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20goaleconomyschedulerz serve --port 8799
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20goaleconomyschedulerz/tests mem20goaleconomyschedulerz/mem20goaleconomyschedulerz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20goaleconomyschedulerz
```

## Absorbed: `mem20intentcompilerz`

# mem20intentcompilerz — Intent Compiler (RM-051, #329)

**Outcome:** Translate goals into typed executable graphs with resources, constraints, and success conditions.
**Breakthrough:** Users can state goals at a high level and still get reliable execution.

Preserves legacy domain API (**compat critical for 300-308 peer set**) and CAPABILITY Engine/CLI/10-scenario simulator (`compose` operation kind).

## Legacy domain API (preserved)
`parse_intent(text)`, `classify(intent)`, `compile_to_action(intent)`, `validate(intent)`, `intent_confidence(intent,keywords)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Intent compilation role (feeds executable outcome) |
|---|---|---|
| `mem20deterministicconfigurationgraphz` | `add_node`,`add_edge`,`resolve` | typed executable resource/constraint/success graph |
| `mem20dynamicskillgraphz` | `add_skill`,`learning_path` | action/capability execution plan |
| `mem20semanticobjectgraphz` | `canonical`,`stable_hash`,`words` | typed intent/entity identity |
| `mem20relationshipcontextgraphz` | `canonical`,`similarity` | goal executability context |
| `mem20reversibleexecutiongraphz` | `create_graph`,`add_node`,`undo` | reversible execution planning |
| `mem20pipez` | `version_asset`,`vc_health` | intent/plan versioning |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20intentcompilerz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20intentcompilerz execute '{"text":"create deployment pipeline","resources":["ci"],"constraints":["safe rollout"],"success_conditions":["pipeline green"]}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20intentcompilerz serve --port 8809
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20intentcompilerz/tests mem20intentcompilerz/mem20intentcompilerz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20intentcompilerz
```

## Absorbed: `mem20prioritycollisionresolverz`

# RM-188 — Priority Collision Resolver

**Owner:** Ariel  
**Lane:** Mission dispatch, execution visibility, and real-time operations

## Outcome
Detect conflicting urgent work and negotiate a feasible execution order

## Breakthrough
The platform handles competing priorities explicitly rather than silently dropping tasks

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-188 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20realtimeteampresencez`

# mem20realtimeteampresencez — Real-Time Team Presence

First-class mem20 subsystem for real-time team presence (set/get presence, online/away users, presence health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20universalhealthnervoussystemz`, `mem20faultcontainmentcellsz`, `mem20selfhealingplansz`, `mem20mixedinitiativefocusenginez`.

## Python API (runnable)
```python
from mem20realtimeteampresencez.domain import set_presence, get_presence, online_users, presence_report, probe
p={}; set_presence(p,"alice","online"); print(get_presence(p,"alice")["status"])  # online
print(online_users(p))  # ['alice']
r=presence_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeteampresencez --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeteampresencez status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeteampresencez doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20realtimeteampresencez serve --port 8813
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/realtimeteampresencez/index.html` (no Vite edits).

## MCP & registration
`RealTimeTeamPresenceToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20realtimeteampresencez/mem20realtimeteampresencez/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20realtimeteampresencez
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
