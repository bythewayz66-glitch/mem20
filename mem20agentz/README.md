# mem20agentz

> mem20 agent platform — all known agent features, built directly into mem20

The agent platform: a conversational tool-calling loop (`AgentCore`), profiles,
sessions, skills, bridges, cron, kanban, and a **grounded-turn pipeline** that
wires the platform into the rest of the estate.

## At a glance

| metric | value |
|---|---|
| python modules | 117 |
| lines of python | 19,900+ |
| test files | 6 |
| console entry points | 2 |

## Entry points

| command | target |
|---|---|
| `mem20agentz` | `mem20agentz.cli:main` |
| `mem20` | `mem20agentz.cli:main` |

## Cross-subsystem wiring (mem20 4.0 criterion 6)

`mem20agentz.ecosystem` is the seam between the agent platform and the rest of
mem20. Every adapter imports a sibling subsystem **and calls it**:

| subsystem | function called | what it answers |
|---|---|---|
| `memory_engine` | `memory.recall` / `memory.remember` | what is grounded, before the agent reasons |
| `mem20crewz` | `guardrails.Guards.check_clearance` | may this plan proceed, epistemically |
| `mem20dreamz` | `verdicts.fidelity_verdict` / `divergence` | did the answer still serve the brief |
| `mem20verify` | `linters.ALL_CHECKS` (each invoked) | is the generated source structurally sound |
| `mem20kilnz` | `budgets.check_triangles` | is the asset within its authored budget |
| `mem20corez` | `mlp.CharMLP.perplexity` | how unlike the corpus is the answer |
| `mem20cliz` | `split_json_flag` / `SCHEMA_VERSION` | the shared `--json` CLI envelope |

`GroundingPipeline.prepare()` runs before the loop, `review()` after it. A
subsystem that is missing or raises is recorded as `{"ok": false, "error": ...}`
and never aborts the turn — but `report.verified` is then `false`, so a caller
can refuse to trust an unverified answer instead of guessing.

## Runnable example

```bash
cd mem20agentz
MEM20_STORE_PATH=/tmp/agentz-demo python3 - <<'PY'
import sys
sys.path.insert(0, "."); sys.path.insert(0, "..")
from mem20agentz.ecosystem import record_turn, run_pipeline

record_turn("agentz.readme", "the prop family triangle budget is 4000 triangles",
            tags=["readme"])

out = run_pipeline(
    "what is the prop triangle budget?",
    "The prop budget is 4000 triangles.\n"
    "```python\ndef within(n):\n    return n <= 6000\n```",
    topic="agentz.readme",
)
print("verified:", out["verified"])
print("subsystems:", out["subsystems"])
print("fidelity:", out["fidelity"]["fidelity"],
      "| lint clean:", out["lint"]["clean"],
      "| budget ok:", out["budget"]["within_budget"],
      "| perplexity:", round(out["confidence"]["perplexity"], 2))
PY
```

Real output of the block above, run on this branch:

```
verified: True
subsystems: ['memory_engine', 'mem20crewz', 'mem20dreamz', 'mem20verify', 'mem20kilnz', 'mem20corez']
fidelity: 50 | lint clean: True | budget ok: True | perplexity: 59.17
```

## MCP surface (criterion 7)

Registered in `mcp/tools/agentz_tools.py` and mixed into `mcp/server.py`:

| tool | what it does |
|---|---|
| `agentz_status` | is the platform importable, and what does it wire to |
| `agentz_ground` | grounded context for a topic (`memory_engine`) |
| `agentz_review` | review an answer against a brief (all six subsystems) |
| `agentz_run` | one conversational turn through `AgentCore`, then reviewed |

## Tests

```bash
cd mem20agentz
python3 -m pytest tests/test_ecosystem.py -q
```

`tests/test_ecosystem.py` asserts on the values the *other* subsystems compute —
a fact written through the adapter is read back by the engine's own `recall`, a
known-bad snippet is caught by `mem20verify`, an over-budget triangle count is
rejected by `mem20kilnz` — so the wiring is exercised, not merely declared.

## Verification

```bash
cd /opt/mem20
python3 scripts/renovation/conformance.py mem20agentz
```

## Absorbed: `mem20multimodaldatanormalizerz`

# RM-166 — Multimodal Data Normalizer

**Owner:** Kimberly  
**Lane:** Schema, data shape, database, and information transformation

## Outcome
Turn text, images, audio, video, and sensor streams into linked structured objects

## Breakthrough
Unstructured media becomes directly usable by applications

This package implements the locally executable/non-human portion of this Off Record Lab roadmap on a shared, zero-dependency runtime substrate. It includes typed/versioned roadmap validation, SQLite WAL state + event history, resumable/idempotent jobs, cancellation/timeouts/quotas, deterministic recovery, adaptive mode decisions with confidence/alternatives/bottlenecks/explanations, feedback tuning, CLI + typed client + HTTP API + browser command surface + event stream, local/hybrid/cloud peer execution, conflict-safe LWW synchronization, caching, backpressure/failover, metrics, simulator scenarios, benchmark tooling, safety gating, and a rollback manifest.

The domain engine for this package is keyed specifically to RM-166 and produces deterministic executable results for the roadmap's core operation using only local standard-library code. External hardware, proprietary models, production credentials, live third-party services, and deployment authorization are intentionally not fabricated; those remain environment-bound integration points.

## Run
```bash
python run.py inspect
python run.py run '{"text":"demo","cache":false}'
python run.py simulate
python run.py benchmark --runs 5
python run.py serve --port 8765
```

Open `http://127.0.0.1:8765/` for the live command surface.
