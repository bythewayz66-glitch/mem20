# mem20dreamz — 4.0 promotion gate

The dream engine. Iteration must **improve**, never **condense**.

## The defect this replaces

`cog/braid_dream_section.py:115` did `st["seed"] = out[:300]`. Every iteration
read a 300-character tail of the previous output, so early structure could not
survive and each pass was a resample rather than a revision. Measured on a real
run before the fix, the artifact oscillated `273 -> 993 -> 246 -> 11625` —
regeneration with a lottery. A lineage now keeps the artifact in full, every
intermediate version, an invention register, and its own evolving config.

## Panel: one model per member

The owner's rule. A single-model panel makes its blind spot *systematic*: every
member can be confidently wrong the same way, and agreement is laundered into
consensus. Eight distinct models, every one verified to answer on this host by a
real call. `assert_roster_valid()` **raises** on a duplicate model — it used to
deduplicate silently, which quietly deleted the `systems_inventor` role and left
the panel with a hole nobody could see.

## Cross-subsystem wiring (mem20 4.0 criterion 6)

A dream is only worth keeping if it is *new* and *true*. The engine already
measures novelty against its own lineage; `mem20dreamz/ecosystem.py` adds the
estate's other half, so a candidate that invents a fact, ships broken code or
blows a triangle budget is caught before promotion.

| subsystem | function called | what it answers |
|---|---|---|
| `memory_engine` | `memory.recall` / `memory.remember` | what the estate already knows about the seed |
| `mem20crewz` | `guardrails.Guards.check_clearance` | may this dream rest on these facts |
| `mem20verify` | `linters.ALL_CHECKS` (each invoked) | is the dream's code structurally sound |
| `mem20kilnz` | `budgets.check_triangles` | is the proposed asset within its authored budget |
| `mem20corez` | `mlp.CharMLP.perplexity` | how unlike the corpus is the candidate |
| `mem20cliz` | `build_envelope` / `split_json_flag` | the fleet's shared `--json` envelope |

`DreamGate.ground()` runs before the dream; `judge()` runs after it. A subsystem
that is missing or raises is recorded as `{"ok": false, "error": ...}` and never
aborts the dream — but `report.promotable` is then `false`, so a caller can
refuse to promote an unverified candidate instead of guessing.

## Runnable example

```bash
cd mem20dreamz
MEM20_STORE_PATH=/tmp/dz-demo python3 - <<'PY'
import sys
sys.path.insert(0, "."); sys.path.insert(0, "..")
from mem20dreamz import ecosystem

out = ecosystem.run_gate(
    "dream.mesh",
    "A lighter prop mesh at 4000 triangles.\n"
    "```python\ndef within(n):\n    return n <= 6000\n```",
)
print("promotable:", out["promotable"])
print("subsystems:", out["subsystems"])
print("lint clean:", out["lint"]["clean"],
      "| budget ok:", out["budget"]["within_budget"],
      "| perplexity:", round(out["distance"]["perplexity"], 2))
PY
```

Real output of the block above, run on this branch:

```
promotable: True
subsystems: ['memory_engine', 'mem20crewz', 'mem20verify', 'mem20kilnz', 'mem20corez']
lint clean: True | budget ok: True | perplexity: 58.84
```

## MCP surface (criterion 7)

Registered in `mcp/tools/dreamz_tools.py` and mixed into `mcp/server.py`:

| tool | what it does |
|---|---|
| `dreamz_status` | is the engine importable, and what does it wire to |
| `dreamz_ground` | what the estate already knows about a seed |
| `dreamz_gate` | judge a candidate before promotion (all five subsystems) |
| `dreamz_estate` | installed vs claimed vs phantom subsystems |

## Tests

```bash
cd mem20dreamz
python3 -m pytest tests/test_ecosystem.py -q
```

`tests/test_ecosystem.py` asserts on the values the *other* subsystems compute —
a dream recorded through the gate is read back by the engine's own `recall` and
labelled `agent_generated`, a known-bad snippet is caught by `mem20verify`, an
over-budget triangle count is rejected by `mem20kilnz` — so the wiring is
exercised, not merely declared.

## Verification

```bash
cd /opt/mem20
python3 scripts/renovation/conformance.py mem20dreamz
```
