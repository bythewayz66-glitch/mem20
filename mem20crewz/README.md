# mem20crewz

**Roadmap-backed multi-agent crews on the mem20 substrate.**

mem20crewz is a cleanroom implementation of Agent / Task / Crew / Flow primitives. Every crew run is a first-class roadmap: phases move planned → in_progress → completed/blocked and are persisted. Reasoning goes through a pluggable Brain (real CogBrain or deterministic FakeBrain for tests). Delegation fans out over A2A peers. Guardrails (epistemic veto, quarantine, plan-execution) are enforced on every step.

Zero dependency on any legacy "mem20 crews" package — this surface imports only mem20 natives.

## Quick start

```bash
# From a clean environment
pip install -e "./mem20crewz[dev]"
python -m pytest mem20crewz/tests -q          # 52 tests

# Offline deterministic demo (no API keys)
python -m mem20crewz.demo.demo_crew --fake
```

## Repository layout

```
mem20crewz/
  __init__.py      public exports
  neural.py        Brain (ABC), CogBrain, FakeBrain
  agents.py        Agent
  tasks.py         Task, TaskOutcome
  crew.py          Crew, CrewResult
  flow.py          Flow
  guardrails.py    Guards (epistemic veto, quarantine, plan-execution)
  roadmap.py       roadmap persistence
  a2a.py           peer delegation
  ecosystem.py     4.0 cross-subsystem governor
  cli.py           operator CLI
  tests/
```

## Cross-subsystem wiring (mem20 4.0 criterion 6)

A crew is a set of agents doing work in sequence, so every crew run is also a
memory, verification and budget question. `ecosystem.py` is that seam — the
crew's own pre-flight/post-flight path.

| subsystem | function called | what it answers |
|---|---|---|
| `memory_engine` | `memory.recall` / `memory.remember` | what is grounded before the crew starts |
| `mem20verify` | `linters.ALL_CHECKS` (each invoked) | is the code the crew produced structurally sound |
| `mem20dreamz` | `verdicts.fidelity_verdict` / `divergence` | does the output still serve the brief |
| `mem20kilnz` | `budgets.check_triangles` | is the claimed asset within its authored budget |
| `mem20corez` | `mlp.CharMLP.perplexity` | how unlike the corpus is the output |
| `mem20cliz` | `build_envelope` / `split_json_flag` | the fleet's shared `--json` envelope |

The epistemic veto (`guardrails.Guards`) is the crew's *own* mechanism and is
not counted as external wiring.

`CrewGovernor.prepare()` runs before the crew; `judge()` runs after it. A
subsystem that is missing or raises is recorded as `{"ok": false, "error": ...}`
and never aborts the crew — but `report.clear` is then `false`, so a caller can
refuse to ship an unverified run instead of guessing.

## Runnable example

```bash
cd mem20crewz
MEM20_STORE_PATH=/tmp/cz-demo python3 - <<'PY'
import sys
sys.path.insert(0, "."); sys.path.insert(0, "..")
import ecosystem

out = ecosystem.run_governor(
    "what is the prop triangle budget?",
    "The prop budget is 4000 triangles.\n"
    "```python\ndef within(n):\n    return n <= 6000\n```",
    topic="crew.readme",
)
print("clear:", out["clear"])
print("subsystems:", out["subsystems"])
print("lint clean:", out["lint"]["clean"],
      "| budget ok:", out["budget"]["within_budget"],
      "| fidelity:", out["fidelity"]["fidelity"],
      "| perplexity:", round(out["surprise"]["perplexity"], 2))
PY
```

Real output of the block above, run on this branch:

```
clear: True
subsystems: ['memory_engine', 'mem20verify', 'mem20dreamz', 'mem20kilnz', 'mem20corez']
lint clean: True | budget ok: True | fidelity: 50 | perplexity: 59.17
```

## MCP surface (criterion 7)

Registered in `mcp/tools/crewz_tools.py` and mixed into `mcp/server.py`:

| tool | what it does |
|---|---|
| `crewz_status` | is the runtime importable, and what does it wire to |
| `crewz_ground` | grounded context before a crew starts |
| `crewz_govern` | judge a crew output before it ships (all five subsystems) |
| `crewz_guard` | the crew's own epistemic veto over a set of fact ids |

## Tests

```bash
cd mem20crewz
python3 -m pytest tests/test_ecosystem.py -q
```

`tests/test_ecosystem.py` asserts on the values the *other* subsystems compute —
a crew outcome recorded through the governor is read back by the engine's own
`recall` and labelled `agent_generated`, a known-bad snippet is caught by
`mem20verify`, an over-budget triangle count is rejected by `mem20kilnz` — so
the wiring is exercised, not merely declared.

## Verification

```bash
cd /opt/mem20
python3 scripts/renovation/conformance.py mem20crewz
```
