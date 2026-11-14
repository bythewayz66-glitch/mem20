# mem20gamez

`mem20gamez` is mem20's native OpenGame-style reinforcement-learning package. It
contains executable torch agents, a deterministic in-package environment,
potential-based reward shaping, performance-gated curriculum, prioritized
replay, independent multi-agent DQN training, and an optional live HTTP server.

No pretrained model, canned learning curve, random fallback environment, or
mock learning loop is used.

## Verified capabilities

| Area | Implemented behavior |
|---|---|
| `environment.py` | `TinyGridWorld-v0` uses a fixed-size one-hot canvas, active-grid difficulty, deterministic movement, optional wind, wall/step penalties, and separate termination/truncation signals. `GymnasiumEnvironment` is a strict optional wrapper; unknown environments fail instead of falling back to synthetic behavior. |
| `reward_shaper.py` | `PotentialBasedShaper` implements `F = scale * (gamma * Phi(s') - Phi(s))`, forces terminal potential to zero, preserves the original reward, and rejects clipping that would break policy invariance. |
| `curriculum.py` | Adaptive difficulty advances or regresses from measured grid progress. It acts once per complete performance window and clamps difficulty to configured bounds. The fixed observation canvas keeps replay and network shapes compatible across stages. |
| `replay_buffer.py` | A deterministic circular prioritized replay with exact-capacity eviction, proportional sampling, annealed importance weights, TD-error priority updates, explicit exact-size batches, and shape-checked NumPy outputs. |
| `agents.py` | Double DQN with a target network, prioritized replay, optional dueling head, hard or Polyak target synchronization, plus REINFORCE, clipped PPO, and discrete SAC gradient implementations. |
| `trainer.py` | Single-agent rollout/evaluation loops and interleaved multi-agent DQN. Every multi-agent instance has its own environment, network, optimizer, target network, and replay buffer. |
| `cli.py` | Training, evaluation, multi-agent training, checkpointing, subsystem checks, and an aiohttp server exposing `/health`, `/reset`, `/act`, `/step`, and `/learn`. |

The behavioral suite proves finite real gradient updates for REINFORCE, PPO, and
SAC. The task-mastery learning assertion and the measured proof below use DQN,
which is the package's fully exercised short-run benchmark.

## Measured DQN proof

Command:

```bash
mem20gamez train \
  --agent dqn \
  --env TinyGridWorld-v0 \
  --grid-size 4 \
  --episodes 80 \
  --eval-episodes 20 \
  --batch-size 32 \
  --update-every 1 \
  --lr 0.01 \
  --gamma 0.99 \
  --shape \
  --seed 7
```

Observed on the root venv with `torch 2.14.0+cpu`:

```text
before_mean_reward -9.730  before_success_rate 0.000
after_mean_reward   9.940  after_success_rate  1.000
first_window_reward 9.576  last_window_reward 9.928
first_window_loss   0.069549  last_window_loss 0.036290
elapsed=6.20 sec
```

Those values come from the run itself. The agent learns the six-step optimal
route on the deterministic 4×4 grid: goal reward `10.0` plus six step penalties
`-0.01` equals `9.94`.

A separate two-agent 2×2 run moved each agent from mean reward `-9.91` to
`9.98`, with greedy success rate `1.00`, in `4.97 sec`.

A 40-episode curriculum run measured the expected 10-episode gates on the 4×4
canvas: difficulty `0.25`, `0.50`, `0.75`, then `1.00` at episodes 10, 20, 30,
and 40. Runtime was `2.19 sec`.

## Install

The runtime requires Python 3.11+, NumPy, torch, PyYAML, and aiohttp.

```bash
cd /opt/mem20/mem20gamez
python3 -m pip install -e .
python3 -m pip install -e ".[dev]"
```

Install Gymnasium only when external Gym environments are needed:

```bash
python3 -m pip install -e ".[gym]"
```

`TinyGridWorld-v0` needs no external environment package.

## Commands

```bash
# Measured 4x4 DQN run
mem20gamez train --agent dqn --env TinyGridWorld-v0 --grid-size 4 \
  --episodes 80 --eval-episodes 20 --batch-size 32 --update-every 1 \
  --lr 0.01 --gamma 0.99 --shape --seed 7

# Save a trained DQN checkpoint
mem20gamez train --agent dqn --shape --checkpoint /tmp/mem20gamez-dqn.pt

# Independent, interleaved DQN agents
mem20gamez multi --agents 2 --grid-size 2 --episodes 35 \
  --batch-size 8 --update-every 1 --lr 0.02 --gamma 0.95 --shape --seed 31

# Live DQN process
mem20gamez serve --env TinyGridWorld-v0 --agent dqn --host 127.0.0.1 --port 8007

# Fast subsystem contract check
mem20gamez test
```

The packaged server is persisted as `mem20gamez.service`, enabled and started
with systemd, so it survives reboot rather than running as a floating process.

## Verification

```bash
cd /opt/mem20/mem20gamez
python3 -m pytest -q
python3 -m ruff check .
```

Current result: `29 passed`, and Ruff reports `All checks passed!`.

## Managed members (package-review integration)

Single-purpose game organs grouped here by reference; they live in their
own top-level directories and are smoke-verified there:

- `mem20ailevelarchitectz`
- `mem20alternativedatabaseplaygroundz`
- `mem20dynamicquestrewardcomposerz`
- `mem20gameproductioncontrolcenterz`
- `mem20simz`

## Absorbed: `mem20ailevelarchitectz`

# mem20ailevelarchitectz — AI Level Architect

Generate room layouts, difficulty curves, enemy placements, and pacing profiles, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20ailevelarchitectz.domain import (
    generate_layout, difficulty_curve, place_enemies, pacing_profile, validate_level, estate_context,
)

layout = generate_layout(width=30, height=20, rooms=5, seed=1)
print(len(layout["rooms"]))
print(difficulty_curve(levels=5))
print(place_enemies(layout, density=0.2, seed=1)[:2])
print(pacing_profile(total_time=120))
print(validate_level(layout))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20ailevelarchitectz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20ailevelarchitectz/mem20ailevelarchitectz/tests -q
```

## Absorbed: `mem20alternativedatabaseplaygroundz`

# RM-108 — Alternative Database Playground

**Owner:** OtherStack  
**Lane:** Experimental and incompatible technology incubator

## Outcome
Benchmark graph, vector, time-series, columnar, and embedded databases against real workloads

## Breakthrough
Each feature can use the storage model that actually fits it

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-108 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.

## Absorbed: `mem20dynamicquestrewardcomposerz`

# mem20dynamicquestrewardcomposerz — Dynamic Quest Reward Composer

First-class mem20 subsystem for dynamic quest and reward composition (quest generation, reward scaling, balancing, quest chains, completion rate) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20communitychallengeenginez`, `mem20dynamicnarrativeenginez`, `mem20eventstreamsuperhighwayz`, `mem20crossproductloyaltygraphz`, `mem20capabilitymarketplacez`, `mem20customerlifecycleenginez`.

## Python API (runnable)
```python
from mem20dynamicquestrewardcomposerz.domain import generate_quest, reward_for_quest, balance_quests, quest_chain, completion_rate, quest_report, probe
q=generate_quest(2,seed=1); print(q["difficulty"])  # 2
print(reward_for_quest(q,1)["xp"]>0)  # True
print(quest_chain([{"difficulty":2},{"difficulty":1}])[0]["difficulty"])  # 1
r=quest_report(); print(r["ok"], len(r["peers"]))  # True 6
print(probe()["ok"])  # True
```

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicquestrewardcomposerz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicquestrewardcomposerz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicquestrewardcomposerz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20dynamicquestrewardcomposerz serve --port 8803
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `GET /api/events|health`. Cockpit `/`. docs/app `docs/app/dynamicquestrewardcomposerz/index.html` (no Vite edits).

## MCP & registration
`DynamicQuestRewardComposerToolsMixin` in `mcp/server.py`; gateway `SUBSYSTEMS`.

## Tests & conformance
```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20dynamicquestrewardcomposerz/mem20dynamicquestrewardcomposerz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20dynamicquestrewardcomposerz
```
Target **7/7**.

## Absorbed: `mem20gameproductioncontrolcenterz`

# mem20gameproductioncontrolcenterz — Game Production Control Center (RM-233, #317)

**Outcome:** operate agent work, builds, assets, testing, engine imports, costs, and releases from one live surface.  
**Breakthrough:** a complete studio pipeline becomes visible and controllable.

Preserves legacy domain API and CAPABILITY Engine/CLI/10-scenario simulator. `simulate` returns `scenarios` (backward compatible) and, with production context, a **meaningful** `production_control` report composed from real domain + peer integrations.

## Legacy domain API (preserved)
`sprint_plan(tasks,capacity)`, `burndown(tasks,completed_ids)`, `milestone_status(milestones,today)`, `risk_score(project)`, `production_health(sprints)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | How it affects production control |
|---|---|---|
| `mem20realtimeteampresencez` | `set_presence`,`online_users` | computes effective team capacity used in sprint planning |
| `mem20uniteconomicsautopilotz` | `ltv`,`cac`,`payback_months`,`ltv_cac_ratio` | projects cost/revenue sustainability |
| `mem20hotswappableservicefoundationz` | `register_service`,`swap`,`health` | assesses build/release service readiness |
| `mem20rewardforgez` | `forge_health` | reports production capability/model readiness |
| `mem20labz` | `resilience_score`,`recovery_time` | adjusts risk via resilience and recovery estimates |
| `mem20pipez` | `create_rig`,`set_pose`,`animate` | reports asset/animation pipeline readiness |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20gameproductioncontrolcenterz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20gameproductioncontrolcenterz execute '{"baseline":1,"production":true,"tasks":[{"id":"t1","effort":3}],"capacity":5,"today":1,"milestones":[{"id":"m1","due_day":5}],"project":{"team_size":4,"budget_ratio":0.9}}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20gameproductioncontrolcenterz serve --port 8797
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20gameproductioncontrolcenterz/tests mem20gameproductioncontrolcenterz/mem20gameproductioncontrolcenterz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20gameproductioncontrolcenterz
```

## Absorbed: `mem20hotswappableservicefoundationz`

# mem20hotswappableservicefoundationz — Hot-Swappable Service Foundation (RM-091, #324)

**Outcome:** Replace running service implementations without stopping unrelated capabilities.
**Breakthrough:** The platform upgrades continuously with near-zero disruption.

Preserves legacy domain API (**#317 peer dependency**) and CAPABILITY Engine/CLI/10-scenario simulator (`analyze` operation kind). `analyze` is meaningful for service/swap payloads and backward-compatible for generic analyze.

## Legacy domain API (preserved for #317)
`register_service(registry,name,impl)`, `swap(registry,name,new_impl)`, `health(registry)`, `rollback(registry,name)`, `list_services(registry)`.

## Meaningful cross-subsystem wiring (criterion 6)
| Peer | Real calls | Hot-swap role (feeds analysis outcome) |
|---|---|---|
| `mem20pipez` | `version_asset`,`diff_versions`,`recover`,`vc_health` | impl versioning and recovery readiness |
| `mem20deterministicconfigurationgraphz` | `add_node`,`add_edge`,`resolve` | deterministic service/config resolution |
| `mem20reversibleexecutiongraphz` | `create_graph`,`add_node`,`undo` | reversible swap/rollback safety model |
| `mem20semanticobjectgraphz` | `words`,`stable_hash`,`canonical` | service identity and semantic hashing |
| `mem20relationshipcontextgraphz` | `canonical`,`similarity` | dependency/continuity context |
| `mem20dynamicskillgraphz` | `add_skill`,`update_proficiency`,`learning_path` | swap/rollback capability readiness path |

## Runnable example (verified)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hotswappableservicefoundationz simulate
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hotswappableservicefoundationz execute '{"service":"api","op":"swap","current_impl":"v1","impl":"v2","config":{"deps":["runtime"]}}'
PYTHONPATH=/opt/mem20 .venv/bin/python -m mem20hotswappableservicefoundationz serve --port 8804
```

## Tests / conformance
```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20hotswappableservicefoundationz/tests mem20hotswappableservicefoundationz/mem20hotswappableservicefoundationz/tests -q --noconftest
PYTHONPATH=/opt/mem20 .venv/bin/python scripts/renovation/conformance.py mem20hotswappableservicefoundationz
```

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

## Absorbed: `mem20uniteconomicsautopilotz`

# mem20uniteconomicsautopilotz — Unit Economics Autopilot

First-class mem20 subsystem for unit economics (ltv/cac/payback/ratio) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20revenueleakhunterz`, `mem20simz`, `mem20simz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20universalhealthnervoussystemz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20uniteconomicsautopilotz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20uniteconomicsautopilotz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20uniteconomicsautopilotz serve --port 8841
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
