# mem20kilnz

A cleanroom, agent-first 3D subsystem for mem20: a C++ geometry kernel driven
over JSON-RPC, wrapped in a Python package with budgets, a read-only glTF
validator, and a CLI that turns a written brief into a real asset.

The human surface is deliberately secondary. The primary caller is an agent.

## What is actually implemented

Everything below is exercised by the test suite or the CLI in this repo. It is
not a roadmap.

- **103 ops** on the C++ kernel, with an automated drift guard
  (`tests/check_op_sync.py`) that fails if the advertised list and the
  dispatcher ever disagree.
- **glTF 2.0 / GLB import and export.** Geometry (positions, indices) round-trips
  without loss. 17 fixtures are covered; malformed files are rejected with a
  reason rather than crashing.
- **OBJ import and export.**
- **Mesh operations** including decimation, normals, booleans, remesh, smoothing,
  subdivision (loop, Catmull-Clark), wireframe, shrinkwrap, symmetrize, extrude,
  bevel, and per-vertex transform ops.
- **Rig operations** including two-bone inverse kinematics, parenting, skinning,
  and pose application.
- **A natural-language and JSON-RPC agent surface.** The engine prefers, in
  order: literal JSON, the kiln DSL, a built-in English intent handler, then an
  LLM.
- **A provenance journal.** Every applied op is recorded with its verdict,
  including the ones a language model invents internally and which never arrive
  at the kernel.
- **Authored triangle budgets** per asset family, with detail tiers and LOD
  ceilings (`mem20kilnz/budgets.py`).

## 4.0 — the build gate (`mem20kilnz/ecosystem.py`)

An asset is only shippable if it is *within budget*, *structurally sound*,
*faithful to its brief* and *grounded in what the estate already knows*. The
build gate is that seam, and it is wired into six other mem20 subsystems.

| subsystem | function actually called | what it decides |
|---|---|---|
| `memory_engine` | `memory.recall`, `memory.remember` | what the estate knows about this asset family; the build outcome is written back as `agent_generated` |
| `mem20crewz` | `guardrails.Guards.check_clearance` | may this build rest on these facts, or is it a guess with a manifest |
| `mem20verify` | `linters.ALL_CHECKS` (every check invoked) | is the emitted code structurally sound |
| `mem20dreamz` | `verdicts.fidelity_verdict`, `verdicts.divergence` | does the result still serve the brief, and how far did it move |
| `mem20corez` | `mlp.CharMLP.perplexity` | how far the result sits from the model's corpus |
| `mem20cliz` | `build_envelope`, `split_json_flag` | the fleet's shared `--json` envelope |

`BuildGate.prepare()` runs before a build; `BuildGate.judge()` runs after it.
`report.shippable` is `True` only when every subsystem that was asked actually
answered — a part that ran and returned `ok: False` makes the report
unshippable, and a part that was never run (a text-only build has no code to
lint) is marked `skipped` rather than counted as a pass.

### Runnable example

```python
import sys
sys.path.insert(0, "mem20kilnz")
sys.path.insert(0, ".")
from mem20kilnz import ecosystem

out = ecosystem.run_gate(
    "build the prop family mesh at the standard budget",
    "Built the prop family mesh at 4000 triangles.\n"
    "```python\ndef within(n):\n    return n <= 6000\n```\n",
    topic="kiln.readme",
)
print(out["shippable"], out["subsystems"])
```

Real output from that call:

```json
{
  "shippable": true,
  "subsystems": [
    "memory_engine",
    "mem20crewz",
    "mem20verify",
    "mem20dreamz",
    "mem20corez"
  ],
  "context": {
    "ok": true,
    "subsystem": "memory_engine",
    "count": 0,
    "rows": []
  },
  "veto": {
    "ok": true,
    "subsystem": "mem20crewz",
    "vetoed": false,
    "reason": "no fact_ids to veto-check",
    "offenders": [],
    "verdict": {
      "vetoed": false,
      "reason": "no fact_ids to veto-check"
    }
  },
  "lint": {
    "ok": true,
    "subsystem": "mem20verify",
    "checks": 4,
    "issues": [],
    "clean": true
  },
  "fidelity": {
    "ok": true,
    "subsystem": "mem20dreamz",
    "fidelity": 50,
    "summary": "lexical overlap with the brief",
    "divergence": 54.0,
    "novelty": 62.5
  },
  "surprise": {
    "ok": true,
    "subsystem": "mem20corez",
    "perplexity": 57.13324529408706,
    "params": 28337
  },
  "recorded": {}
}
```

### MCP surface

`mcp/tools/kilnz_tools.py` registers four tools on the mem20 MCP server:

- `kilnz_status` — is the kiln importable, and what does it wire to
- `kilnz_ground` — grounded context about an asset family before a build
- `kilnz_gate` — judge a build result before the asset ships
- `kilnz_budget` — check a triangle count against the authored budget table

### Tests

```bash
python3 -m pytest mem20kilnz/tests/test_ecosystem.py -q
# 13 passed
```

The tests assert on the value the *other* subsystem computed — a build recorded
through the gate is read back by the engine's own `recall` and labelled
`agent_generated`; the veto refuses a build on agent output and passes one on
user-stated facts; a known-bad snippet is caught by `identical-branches`; the
perplexity is a finite number from real matrix multiplication.

### Conformance

```bash
python3 scripts/renovation/conformance.py mem20kilnz
```
