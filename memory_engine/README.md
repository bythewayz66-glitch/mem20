# memory_engine

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
