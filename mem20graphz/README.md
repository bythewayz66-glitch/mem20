# mem20graphz — graph crew runtime (#321)

mem20 graph systems runtime. Preserves `MEMBERS`, `__version__`, and legacy CLI (`--version`, `--members`).

## Members (7)
- `mem20capabilitygapmapperz` — capability gap mapping utilities (canonical/hash/terms)
- `mem20crossproductloyaltygraphz` — loyalty graph edges/degree/centrality
- `mem20deterministicconfigurationgraphz` — deterministic config graph resolve
- `mem20dynamicskillgraphz` — dynamic skill graph/proficiency/learning path
- `mem20relationshipcontextgraphz` — relationship context canonical/similarity
- `mem20reversibleexecutiongraphz` — reversible execution graph nodes/undo
- `mem20semanticobjectgraphz` — semantic object terms/hashing

## Meaningful cross-subsystem wiring (criterion 6)
Real imports and calls to all 7 member subsystems, exercised by `tests/test_graphz_crew.py` and surfaced via `doctor`.

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20graphz --version
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20graphz --members
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20graphz doctor
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20graphz serve --port 8801
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20graphz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20graphz
```

## Absorbed: `mem20capabilitygapmapperz`

# RM-200 — Capability Gap Mapper

**Owner:** Patricia  
**Lane:** Executable planning, dependency modeling, and build sequencing

## Outcome
Compare desired features with available runtimes, models, connectors, and skills

## Breakthrough
The system identifies exactly what must be built or acquired next

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-200 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20crossproductloyaltygraphz`

# mem20crossproductloyaltygraphz — Cross-Product Loyalty Graph

First-class mem20 subsystem for cross-product loyalty graphs (edges, degree, centrality, recommendations, loyalty score) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app, and real MCP tools. Core API preserved.

## Peers (6)
`mem20customerlifecycleenginez`, `mem20simz`, `mem20autonomoussaleslaboratoryz`, `mem20communitychallengeenginez`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20crossproductloyaltygraphz.domain import add_edge, degree, centrality, recommend_products, loyalty_score, loyalty_report, probe
g={}; add_edge(g,"a","b",1); print(degree(g,"a"))  # 1
add_edge(g,"a","c"); print(centrality(g)["a"])     # 1.0
print(recommend_products(g,["a"],1)[0]["product"]) # b or c
print(loyalty_score(["a"],g) > 0)                   # True
r=loyalty_report(); print(r["ok"], len(r["peers"])) # True 6
print(probe()["ok"])                                # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20crossproductloyaltygraphz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20crossproductloyaltygraphz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20crossproductloyaltygraphz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20crossproductloyaltygraphz serve --port 8796
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/crossproductloyaltygraphz/index.html` (no Vite edits).

## MCP & registration
`CrossProductLoyaltyGraphToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20crossproductloyaltygraphz/mem20crossproductloyaltygraphz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20crossproductloyaltygraphz
```
Target **7/7**.

## Absorbed: `mem20deterministicconfigurationgraphz`

# mem20deterministicconfigurationgraphz — Deterministic Configuration Graph

First-class mem20 subsystem for deterministic configuration graphs (nodes/edges, dependency resolution, validation/cycle detection, config diff) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20eventstreamsuperhighwayz`, `mem20faultcontainmentcellsz`, `mem20selfhealingplansz`, `mem20universalhealthnervoussystemz`, `mem20zerotouchnodeswarmz`, `mem20capabilitymarketplacez`.

## Python API (runnable)
```python
from mem20deterministicconfigurationgraphz.domain import add_node, add_edge, resolve, validate, diff_configs, config_report, probe
g={}; add_node(g,"p",{"a":1}); add_node(g,"c",{"b":2}); add_edge(g,"p","c")
print(resolve(g,"c"))  # {'a': 1, 'b': 2}
print(validate(g)["valid"])  # True
print("x" in diff_configs({"x":1},{"x":2}))  # True
r=config_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20deterministicconfigurationgraphz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20deterministicconfigurationgraphz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20deterministicconfigurationgraphz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20deterministicconfigurationgraphz serve --port 8800
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/deterministicconfigurationgraphz/index.html` (no Vite edits).

## MCP & registration
`DeterministicConfigurationGraphToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20deterministicconfigurationgraphz/mem20deterministicconfigurationgraphz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20deterministicconfigurationgraphz
```
Target **7/7**.

## Absorbed: `mem20dynamicskillgraphz`

# mem20dynamicskillgraphz — Dynamic Skill Graph

First-class mem20 subsystem for dynamic skill graphs (skills, prerequisites, proficiency, learning paths, skill gaps, stats) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20capabilitymarketplacez`, `mem20dynamicquestrewardcomposerz`, `mem20customerlifecycleenginez`, `mem20eventstreamsuperhighwayz`, `mem20causalroutingbrainz`, `mem20rewardforgez`.

## Python API (runnable)
```python
from mem20dynamicskillgraphz.domain import add_skill, update_proficiency, learning_path, skill_gap, graph_stats, skill_report, probe
g={}; add_skill(g,"a"); add_skill(g,"b",["a"]); update_proficiency(g,"a",0.8)
print(learning_path(g,"b"))  # ['a', 'b']
print(skill_gap(g,["a"])[0]["gap"])  # 0.2
r=skill_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicskillgraphz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicskillgraphz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicskillgraphz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicskillgraphz serve --port 8804
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/dynamicskillgraphz/index.html` (no Vite edits).

## MCP & registration
`DynamicSkillGraphToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20dynamicskillgraphz/mem20dynamicskillgraphz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20dynamicskillgraphz
```
Target **7/7**.

## Absorbed: `mem20relationshipcontextgraphz`

# RM-114 — Relationship Context Graph

**Owner:** Sherry  
**Lane:** Human communication, presence, and relationship intelligence

## Outcome
Track shared projects, commitments, preferences, and interaction history across contacts

## Breakthrough
Conversations begin with useful context instead of repeated explanations

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-114 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20reversibleexecutiongraphz`

# RM-052 — Reversible Execution Graph

Outcome: Make every multi-step action capable of compensation, pause, branch, and rollback

Breakthrough: Autonomous systems can recover from mistakes without restarting everything

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `graph` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Install

mem20 is **not on PyPI**. Install from source:

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -r requirements.txt
```

## Run the CLI

```bash
cd mem20/mem20reversibleexecutiongraphz
python3 -m mem20reversibleexecutiongraphz simulate
```

## Runnable example: execute a reversible plan

`execute_reversible_plan()` records each step on the graph and audits the run
against the rest of the estate — credential screening (`mem20secretz`), per-step
budget (`mem20kilnz`), grounded ledger write + read-back (`memory_engine`),
store round-trip (`mem20verify`), estate registration (`toolchest`), and the
fleet registry (`gateway`). `reversible` is True only when every step was
accepted and the graph cursor sits on the last node, i.e. the whole run can be
undone.

```python
import json
import sys

# run from the mem20 repo root
sys.path.insert(0, "mem20reversibleexecutiongraphz")

from mem20reversibleexecutiongraphz.integration import execute_reversible_plan

report = execute_reversible_plan(
    plan_id="p1",
    steps=[
        {"id": "s1", "payload": {"op": "resize"}, "triangles": 3000},
        {"id": "s2", "payload": {"op": "retexture"}, "triangles": 4000},
    ],
    family="prop",
)

print(json.dumps(report, indent=2, sort_keys=True))
print("reversible:", report["reversible"])
```

Real output from that script:

```text
{
  "budgets": [
    {
      "ok": true,
      "reason": "within standard 2000-6000",
      "step": "s1"
    },
    {
      "ok": true,
      "reason": "within standard 2000-6000",
      "step": "s2"
    }
  ],
  "fleet": {
    "agents": 0
  },
  "health": {
    "cursor": 1,
    "history": 2,
    "nodes": 2
  },
  "integrity": {
    "checked": 11,
    "error": "",
    "ok": true,
    "roundtrip_ok": 11
  },
  "inventory": {
    "entries": 312,
    "path": "/workspace/mem20/toolchest/inventory.json",
    "subsystem_registered": true
  },
  "ledger": {
    "ok": true,
    "rows": 4,
    "topic": "plan.p1"
  },
  "ok": true,
  "plan_id": "p1",
  "refused": [],
  "reversible": true,
  "secrets": []
}
reversible: True
```

A step whose payload carries a credential, or whose triangle count is outside
its family budget, is listed in `refused` and the run reports
`reversible: false` — the plan is not silently half-applied.

`rollback_plan()` undoes every step and records the rollback in the ledger.

## MCP surface

Registered with the mem20 MCP server as `graph_execute_reversible_plan`
(`mcp/tools/rm052_tools.py`):

```json
{"plan_id": "p1", "steps": [{"id": "s1", "payload": {"op": "resize"}, "triangles": 3000}]}
```

## Tests

```bash
python3 -m pytest mem20reversibleexecutiongraphz -q
```

## Absorbed: `mem20semanticobjectgraphz`

# RM-164 — Semantic Object Graph

**Owner:** Kimberly  
**Lane:** Schema, data shape, database, and information transformation

## Outcome
Unify relational, document, vector, graph, and event views of the same objects

## Breakthrough
Data can be queried in the form best suited to the problem

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-164 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

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
