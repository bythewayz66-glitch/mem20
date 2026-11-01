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

---

The mem20 tiered memory subsystem: an append-only ledger, a deep store, and
three retrieval indexes (vector, BM25, entity graph) with bi-temporal recall and
a hard grounded/simulated separation.

## Public surface

`memory_engine` declares its surface in `__all__` (50 names). Everything else
reachable through `memory_engine.memory.<name>` is internal and may change
without notice.

```python
import os
os.environ["MEM20_STORE_PATH"] = "/var/lib/mem20/store"   # before first import

from memory_engine import MemoryEngine, EngineConfig

engine = MemoryEngine()
fact = engine.remember(
    "thestack.topology",
    "the gateway sits in front of the memory engine",
    epistemic_status="observed",     # required — see "Trust model"
    tags=["architecture"],
)
print(fact.id, fact.epistemic_status, fact.is_trusted)

for f in engine.recall(topic="thestack.topology", k=5):
    print(f.ts, f.content)

print(engine.health().to_dict())
```

### What is stable

| Group | Names |
|---|---|
| Facade | `MemoryEngine`, `Fact`, `HealthReport` |
| Config | `EngineConfig`, `DEFAULT_STORE_PATH` |
| Errors | `MemoryEngineError`, `ConfigurationError`, `ValidationError`, `EpistemicStatusError`, `EventTimeError`, `GroundedWriteRefused`, `IndexDriftError`, `StoreUnavailableError`, `NotFoundError`, `DependencyUnavailableError`, `TransientError` |
| Resilience | `RetryPolicy`, `call_with_retry`, `idempotency_key` |
| Vocabulary | `EPISTEMIC_STATUSES`, `UNLABELED` |
| Engine functions | `remember`, `remember_simulated`, `recall`, `recall_at`, `recall_semantic`, `recall_hybrid`, `recall_graph`, `supersede`, `rebuild_*`, `index_health`, `status`, `ledger_view`, `backup`, `detect_secrets`, `redact_secrets`, `detect_knowledge_gaps`, `self_audit`, `label_coverage`, `audit_contamination`, `promote_simulated_to_grounded`, `quarantine_expired_simulated`, `list_simulated`, `validate_epistemic_status`, `validate_event_time`, `main` |

## Trust model

`remember()` requires an explicit `epistemic_status` from
`observed | inferred | imagined | user_stated | hypothesis | agent_generated`,
or the honest `unlabeled`. It refuses an undeclared basis rather than defaulting
one, because a silently-defaulted label is indistinguishable from an asserted
one at every later read.

Simulated content cannot enter the grounded ledger. `remember(_allow_simulated=True)`
raises `GroundedWriteRefused`; the only sanctioned path is
`remember_simulated()`, which writes to a separate partition with a TTL and
never touches the retrieval indexes.

## Error model

Every deliberate failure is a `MemoryEngineError` subclass carrying a stable
`code` and a `to_dict()` for API serialisation. Each also inherits the builtin
it replaces (`ValueError`, `PermissionError`, `RuntimeError`, `LookupError`,
`OSError`), so existing handlers keep working.

```python
from memory_engine import EpistemicStatusError, RetryPolicy, call_with_retry, TransientError

try:
    engine.remember("topic", "content")
except EpistemicStatusError as exc:
    print(exc.code, exc.details)      # epistemic_status_error, {}

# Retry only what is safe to retry.
call_with_retry(flaky_write, policy=RetryPolicy(max_attempts=3, base_delay=0.05))
```

`RetryPolicy` caps the delay at `max_delay` **before** applying jitter, so the
cap is a real upper bound. `call_with_retry` retries only `TransientError` by
default and re-raises the last real exception when attempts are exhausted.

`idempotency_key(*parts)` gives a deterministic 64-char key for a logical write.
`remember()` mints a random id per call, so a retried write duplicates unless
the caller dedupes on this key.

## Configuration

`EngineConfig` validates the whole surface once, at startup, instead of raising
from deep inside a call.

| Variable | Default | Meaning |
|---|---|---|
| `MEM20_STORE_PATH` | `~/.mem20/store` | Store root. Must be absolute. |
| `MEM20_SIM_TTL_DAYS` | `30` | Simulated-fact decay window. |
| `MEM20_RERANK` | `1` | Cross-encoder reranking on/off. |
| `MEM20_RERANK_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Rerank model. |

The engine resolves its store at **import time**. Set the environment before the
first `memory_engine` access, or call `EngineConfig.apply()` first.

## CLI

```bash
python3 -m memory_engine.memory remember --topic t --content "..." --epistemic-status observed
python3 -m memory_engine.memory recall --topic t --k 5
python3 -m memory_engine.memory status
python3 -m memory_engine.memory rebuild
```

## Tests

```bash
python3 -m pytest memory_engine/tests -q
```

`test_contract.py` is the executable definition of the surface: it fails if a
declared name stops resolving, if a return type changes, or if the facade grows
its own copy of the engine logic. `test_properties.py` uses Hypothesis to assert
invariants over generated inputs.

## Status

M0 (importable core contract) is shipped. See `docs/GAP-INVENTORY.md` for the
12-surface audit with file:line evidence, `docs/INCREMENT-PLAN.md` for the
ordered roadmap, and `docs/EVIDENCE.md` for verbatim command output.
