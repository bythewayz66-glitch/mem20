# memory_engine

The mem20 memory engine: a grounded, epistemically-labelled ledger with hybrid
retrieval, plus the **4.0 substrate** — the stable public API the rest of the
estate wires against.

`memory_engine` is a **gate module** for the 4.0 renovation: waves 2-3 build on
the API below, so it lands first.

## Install

mem20 is **source-only** — it is not published on PyPI, so there is no
`pip install mem20`. Clone and install the requirements:

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20
pip install -r requirements.txt
```

The semantic half of retrieval (sentence-transformers + faiss) is the optional
`vector` extra. Without it the engine falls back to BM25 and says so — it does
not pretend to have run a vector search:

```bash
pip install -e ".[vector]"
```

## Quick start — the substrate

```bash
export MEM20_STORE_PATH=$(mktemp -d)

python3 -m memory_engine remember \
  --topic demo --content "the sky is blue" --epistemic-status observed

python3 -m memory_engine recall --topic demo
python3 -m memory_engine health
```

Real output from the commands above:

```console
$ python3 -m memory_engine remember --topic demo --content "the sky is blue" --epistemic-status observed
{
  "epistemic_status": "observed",
  "id": "f3c1a0e2-...",
  "topic": "demo"
}

$ python3 -m memory_engine recall --topic demo
[
  {
    "content": "the sky is blue",
    "epistemic_status": "observed",
    "id": "f3c1a0e2-...",
    "origin": "grounded",
    "topic": "demo"
  }
]

$ python3 -m memory_engine health
{
  "bm25_available": true,
  "grounded_facts": 1,
  "label_coverage": 1.0,
  "labeled_facts": 1,
  "ledger_events": 1,
  "public_api": ["remember_fact", "recall_facts", "veto_plan", "guard_plan",
                 "namespace_for_agent", "subsystem_status", "envelope",
                 "health", "dream_lineage", "validate_artifact"],
  "store": "/tmp/tmp.XXXXXXXX",
  "vector_available": false
}
```

## Quick start — from Python

```python
from memory_engine import substrate as S

rec = S.remember_fact("demo", "the sky is blue", epistemic_status="observed")

# The label survives the round trip; a record with no recorded basis comes
# back as "unlabeled" rather than with the field missing.
rows = S.recall_facts("demo")
assert rows[0]["epistemic_status"] == "observed"

# May a plan rest on this fact? The engine answers, and reports ids that
# resolve to nothing instead of ignoring them.
verdict = S.veto_plan([rec["id"]])
assert verdict["veto"] is False

# The same question through mem20crewz's guardrail bundle, so a crew and a
# direct caller cannot disagree about whether a plan runs.
guard = S.guard_plan([rec["id"]])
assert guard["blocked"] is False
```

## Public API (stable for 4.0)

| function | what it answers | owned by |
|---|---|---|
| `remember_fact(topic, content, *, epistemic_status, ...)` | store a grounded fact; refuses an undeclared basis | `memory_engine.memory` |
| `recall_facts(topic=None, *, tags, k, include_simulated)` | recall with the label intact | `memory_engine.memory` |
| `veto_plan(fact_ids, *, actor)` | may a plan rest on these ids? | `memory_engine.memory` |
| `guard_plan(fact_ids, *, actor)` | the same, through the crew guardrails | `mem20crewz` |
| `namespace_for_agent(name)` | the memory namespace an agent owns | `mem20agentz` |
| `subsystem_status(name)` | is a subsystem installed, and what does it expose? | `toolchest` |
| `envelope(command, argv, exit_code, ...)` | the fleet JSON envelope | `mem20cliz` |
| `health()` | measured state of the whole substrate | `memory_engine` |
| `dream_lineage(seed, *, kind)` | open a dream lineage, report its artifact | `mem20dreamz` |
| `validate_artifact(path)` | validate a glTF/GLB before trusting it | `mem20kilnz` |

`PUBLIC_API` is the tuple of these names; a test asserts every declared name is
callable, so the table cannot drift from the code.

## CLI

```bash
python3 -m memory_engine status
python3 -m memory_engine remember --topic t --content "..." --epistemic-status observed
python3 -m memory_engine recall --topic t
python3 -m memory_engine veto --id <fact-id>
python3 -m memory_engine guard --id <fact-id>
python3 -m memory_engine namespace --agent "my agent"
python3 -m memory_engine subsystem --name mem20kilnz
python3 -m memory_engine dream --seed "a seed"
python3 -m memory_engine validate --path model.gltf
python3 -m memory_engine health
```

Add `--json` to any subcommand for the fleet envelope. `validate` exits non-zero
when the artifact is invalid, so a script cannot mistake a bad artifact for a
good one.

## MCP

The substrate is registered with the mem20 MCP server as six tools
(`mcp/tools/memory_engine_tools.py`):

`memory_engine_health`, `memory_engine_recall`, `memory_engine_veto`,
`memory_engine_guard`, `memory_engine_namespace`, `memory_engine_subsystem`.

## Tests

```bash
python3 -m pytest memory_engine -q
```

## Notes for 4.0

- **No `pip install mem20`.** mem20 is source-only; every README in the estate
  says clone + `pip install -r requirements.txt`.
- **`MEM20_STORE_PATH`** selects the store (default `~/.mem20/store`). The
  engine resolves it at import time, so set it before importing.
- **`MEM20_ROOT`** tells `toolchest` where the estate lives (default
  `/opt/mem20`). On a source-only clone the substrate points it at the repo root
  automatically.
