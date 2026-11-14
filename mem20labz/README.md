# mem20labz — crew runtime (unified lab subsystem)

Unified lab subsystem consolidating experimental/lab runtimes under `mem20labz/labs/`.

mem20 laboratory runtime.

## Members (10)

Reviewed packages grouped here for joint integration under the
package-review rulings:

- `mem20autonomoussaleslaboratoryz`
- `mem20labz`
- `mem20twinz`
- `mem20labz`
- `mem20labz`
- `mem20labz`
- `mem20labz`
- `mem20simz`
- `mem20labz`
- `mem20labz`

## Status

Skeleton slice: registry, CLI (`--version`, `--members`), hermetic
tests. Member wiring arrives in the integration phase.

## CLI (runnable)

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20labz --version
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20labz --members
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20labz status
```

## Absorbed: `mem20autonomoussaleslaboratoryz`

# mem20autonomoussaleslaboratoryz — Autonomous Sales Laboratory

First-class mem20 subsystem for sales experiments: score leads, generate outreach, estimate conversion, value pipelines, and segment leads — with **6 sales-lab-specific estate peers** (anti-spam guarded; no generic template), SQLite WAL runtime, CLI, JSON HTTP API, served cockpit, docs/app integration, and real MCP tools.

## Peers (6, sales-lab specific)
| peer | real functions | role |
|---|---|---|
| `mem20loreragcontentgeneratorz` | `generate,rank_adapters,quality_score` | approved outreach content/quality |
| `mem20antiexploitationrewardshieldz` | `RewardShield` evaluate/exploit_ratio | anti-spam/guardrail corroboration |
| `mem20causalroutingbrainz` | `DemandForecastAndCapacityBrain` | demand/timing signal |
| `mem20eventstreamsuperhighwayz` | `create_stream,publish,throughput` | experiment events |
| `mem20autonomousdealdeskz` | `price_deal,approval_required,negotiate_round` | deal handoff/pricing context |
| `mem20capabilitymarketplacez` | `CapabilityMarketplace` add/locate/distribution | channel/capability routing |

## Python API
```python
from mem20autonomoussaleslaboratoryz.domain import (
    lead_score, outreach_message, conversion_probability, pipeline_value, segment_leads,
    lab_report, probe, estate_context,
)
lead = {"name":"Bob","email":"b@x.com","budget":2000,"authority":True,"need":True,"timeline_days":10,"deal_value":1000}
print(lead_score(lead)); print(conversion_probability(lead,3)); print(pipeline_value([lead])); print(segment_leads([lead]))
report = lab_report([lead]); print(report["ok"], report["pipeline_value"], len(report["peers"]))  # 6
print(probe()["ok"])
```

## CLI
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussaleslaboratoryz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussaleslaboratoryz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussaleslaboratoryz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussaleslaboratoryz simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomoussaleslaboratoryz serve --port 8785
```

## HTTP API & web/docs
`GET/POST /api/status`, `/api/doctor`, `POST /api/simulate`, `POST /api/score`, `GET /api/events|health`. Cockpit at `/`. State: `~/.mem20/autonomoussaleslaboratoryz/state.sqlite3` (SQLite WAL). docs/app: `docs/app/autonomoussaleslaboratoryz/index.html` (no Vite edits).

## MCP & registration
`AutonomousSalesLaboratoryToolsMixin` (`mcp/tools/mem20autonomoussaleslaboratoryz_tools.py`) in `mcp/server.py`. Gateway `SUBSYSTEMS` entry.

## Tests & conformance
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20autonomoussaleslaboratoryz/mem20autonomoussaleslaboratoryz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20autonomoussaleslaboratoryz
```
Target **7/7**.

## Limits
Deterministic experiment logic; real channel delivery/CRM/consent systems are target-environment integrations. Guardrails/peer failures surfaced, not fatal.

## Absorbed: `mem20adversarialqacrewz`

# mem20adversarialqacrewz — Adversarial QA Crew

Generate adversarial test cases, score mutations, fuzz inputs, and produce release verdicts, with mem20 estate integration.

## Python API

```python
import tempfile
from mem20adversarialqacrewz.domain import (
    generate_adversarial_cases, mutation_score, fuzz_input, verdict, hash_case, estate_context,
)

cases = generate_adversarial_cases({"base_input": {"value": 5}}, count=6)
print(len(cases), cases[0]["mutation"])
print(mutation_score("abc", "axc"))
print(fuzz_input({"x": 5, "s": "a"}, seed=1))
print(verdict([{"pass": True}, {"pass": False}]))
print(hash_case({"a": 1}))

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20adversarialqacrewz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20adversarialqacrewz/mem20adversarialqacrewz/tests -q
```

## Absorbed: `mem20antiexploitationrewardshieldz`

# mem20antiexploitationrewardshieldz — Anti-Exploitation Reward Shield

Corroboration-based reward shielding to resist reward hacking (Goodhart's law), with mem20 estate integration.

## Python API

```python
import tempfile
from mem20antiexploitationrewardshieldz.domain import RewardShield, estate_context

shield = RewardShield(corroboration_tolerance=0.5)
print(shield.evaluate(1.0, {"x": 0}))
print(shield.evaluate(1.0, {"x": 1}))
print(shield.stats)

with tempfile.TemporaryDirectory() as d:
    print(estate_context(d)["engine_status_checked"])
```

## CLI

```bash
python -m mem20antiexploitationrewardshieldz --help
```

## Tests

```bash
PYTHONPATH=/opt/mem20 python -m pytest mem20antiexploitationrewardshieldz/mem20antiexploitationrewardshieldz/tests -q
```

## Absorbed: `mem20autonomousdealdeskz`

# mem20autonomousdealdeskz — Autonomous Deal Desk

First-class mem20 subsystem for autonomous deal operations: price deals, score terms, gate approvals, negotiate rounds, and assess deal health. Real runtime with **6 subsystem-specific estate peers** (deal-desk fit — **not** a generic template), SQLite WAL event log, CLI, JSON HTTP API, served cockpit, docs/app integration, and real MCP tools.

## Architecture

- `domain.py` — pure deal ops + `deal_report()`/`probe()`/`estate_context()`
- `ecosystem.py` — 6 adapters (bootstrap); failures reported `{"ok": false, "error": ...}`, never fatal
- `runtime.py` — `Service` + SQLite WAL `EventStore`; CLI; `ThreadingHTTPServer` JSON API; serves `web/`
- `web/` — vanilla operator cockpit (no build)
- `docs/PLAN.md`, `docs/app/autonomousdealdeskz/` estate monitor, gateway entry, MCP mixin

## Ecosystem peers (6, subsystem-specific)

| peer | real functions | role |
|---|---|---|
| `mem20simz` | `revenue`, `profit`, `margin`, `scenario_sim` | deal economics/margin/scenarios |
| `mem20causalroutingbrainz` | `DemandForecastAndCapacityBrain` (observe/forecast/capacity_for) | demand signal & capacity headroom |
| `mem20acquisitionandpartnershipscoutz` | `target_score`, `strategic_fit`, `rank_targets`, `synergy_estimate` | partnership/strategic fit & synergy |
| `mem20antiexploitationrewardshieldz` | `RewardShield.evaluate`/`exploit_ratio` | approval guardrail/corroboration |
| `mem20capabilitymarketplacez` | `CapabilityMarketplace` (add/locate/distribution) | capability routing via consistent hashing |
| `mem20autonomoussaleslaboratoryz` | `pipeline_value`, `conversion_probability`, `segment_leads` | pipeline value/conversion/segments |

## Python API

```python
from mem20autonomousdealdeskz.domain import (
    price_deal, terms_score, approval_required, negotiate_round, deal_health,
    deal_report, probe, estate_context,
)

print(price_deal({"price": 1000}, {"volume": 500}))
print(terms_score({"payment_days": 15, "contract_months": 12, "auto_renew": True}))
print(approval_required(9500, threshold=10000))
print(negotiate_round(1000, 850, rounds_left=2))
print(deal_health({"signed": True, "paid": False}))

report = deal_report(product={"price": 1200}, customer={"volume": 400}, deal={"deal_value": 1100})
print(report["ok"], report["price"], len(report["peers"]))  # True, ..., 6
print(probe()["ok"])  # True (all peers reachable)
```

## CLI

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz --help
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz simulate
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz serve --port 8782
```

## HTTP API & web cockpit

`GET/POST /api/status`, `GET/POST /api/doctor`, `POST /api/simulate`, `POST /api/price`, `POST /api/negotiate`, `GET /api/events`, `GET /api/health`. Cockpit served at `/` (static `web/`, no build). State: `~/.mem20/autonomousdealdeskz/state.sqlite3` (SQLite WAL) or `--store`/`MEM20_DEALDESK_STORE`.

```bash
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20autonomousdealdeskz serve --port 8782
# cockpit: http://127.0.0.1:8782/  |  estate monitor: docs/app/autonomousdealdeskz/index.html
```

## MCP & registration

MCP: `AutonomousDealDeskToolsMixin` (`mcp/tools/mem20autonomousdealdeskz_tools.py`) registered in `mcp/server.py` (`autonomousdealdeskz_status|doctor|price`). Gateway: `gateway/mem20_gateway.py` SUBSYSTEMS entry. docs/app linked from `docs/app/README.md` (no compiled Vite assets edited).

## Tests & conformance

```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m pytest mem20autonomousdealdeskz/mem20autonomousdealdeskz/tests -q --noconftest -p no:cacheprovider
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python scripts/renovation/conformance.py mem20autonomousdealdeskz
node --check mem20autonomousdealdeskz/mem20autonomousdealdeskz/web/app.js
```

Target: **7/7**.

## Limits

- Pricing/negotiation logic is deterministic rules for this subsystem; real commercial/legal/ERP integrations are target-environment concerns.
- Peer unavailability is surfaced in report/probe and does not crash core operations.

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

## Absorbed: `mem20syntheticevaluatorarenaz`

# mem20syntheticevaluatorarenaz — Synthetic Evaluator Arena

First-class mem20 subsystem for synthetic evaluation arena (create_arena/evaluate/leaderboard/arena_health) with **6 peers**, SQLite WAL runtime, CLI, JSON HTTP API, served web cockpit, docs/app monitor, and real MCP tools. Core API preserved.

## Peers (6)
`mem20collectivemodelintelligencez`, `mem20simz`, `mem20agentoutputcompilerz`, `mem20eventstreamsuperhighwayz`, `mem20capabilitymarketplacez`, `mem20faultcontainmentcellsz`.

## CLI (runnable)
```bash
cd /opt/mem20
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20syntheticevaluatorarenaz status
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20syntheticevaluatorarenaz doctor
PYTHONPATH=/opt/mem20 /opt/mem20/.venv/bin/python -m mem20syntheticevaluatorarenaz serve --port 8839
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
