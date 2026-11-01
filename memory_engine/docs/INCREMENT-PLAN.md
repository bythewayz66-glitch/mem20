# memory_engine — Increment Plan

**Baseline:** `d99ab5d8e9c5c45a1fb3d02d3b65b2f9a96b5110`
**Owner:** mem20-sybsystems
**Rule:** each increment is independently shippable and independently revertable.
No increment depends on a later one.

---

## M0 — Importable core contract ✅ SHIPPED

**Goal:** make the subsystem importable as a declared, typed surface.

| Deliverable | File |
|---|---|
| Typed facade | `memory_engine/api.py` |
| Error model + retry + idempotency | `memory_engine/errors.py` |
| Validated config | `memory_engine/config.py` |
| Declared surface (`__all__`, 50 names) | `memory_engine/__init__.py` |
| Contract tests (20) | `memory_engine/tests/test_contract.py` |
| Error-model tests (26) | `memory_engine/tests/test_error_model.py` |
| Property-based tests (14) | `memory_engine/tests/test_properties.py` |

**Acceptance:** 60 new tests pass; zero regressions in the pre-existing suite;
`import memory_engine` does not import numpy/faiss/sentence-transformers.

**Design decision — the facade delegates, it does not reimplement.**
`MemoryEngine.remember()` calls `memory_engine.memory.remember()`. There is one
implementation of the logic. `test_contract.py::TestNoDrift` asserts the facade
contains no `open(` and no `json.load`, so a future contributor cannot quietly
grow a second implementation inside the facade.

**Design decision — typed errors keep their builtin bases.**
`EpistemicStatusError` subclasses `ValueError`; `GroundedWriteRefused`
subclasses `PermissionError`. Every existing `except ValueError` in the 20
consumer call sites keeps working. This is what makes M0 additive rather than
breaking.

**Bug found and fixed during M0:** the facade originally re-read
`os.environ` at construction while the engine had already resolved its store at
import time. The two could disagree — the facade would report one store while
the engine wrote to another. `MemoryEngine.__init__` now binds to
`engine.STORE_DIR`. Caught by `test_engine_constructs_without_touching_store`.

---

## M1 — Persistence adapter boundary

**Goal:** make the storage backend swappable without editing the engine.

**Problem:** `memory.py:111-125` builds every path from `STORE_DIR` at import
time. A Postgres or S3 backend means editing 4,800 lines.

**Plan:**
1. Define `StoreAdapter` protocol: `append(record)`, `read_all()`, `exists()`,
   `write_index(name, bytes)`, `read_index(name)`.
2. Implement `FilesystemStore` wrapping the current behaviour exactly — this is
   a pure refactor, byte-identical on disk, verified by running the existing
   suite unchanged.
3. Route `_append_ledger` / `_load_ledger` / index I/O through the adapter.
4. Add `MemoryEngine(store=...)` injection point.

**Acceptance:** existing 90 tests pass with `FilesystemStore`; a new
`InMemoryStore` passes the same contract suite; no behaviour change on disk.

**Risk:** this touches the write path of a live store. Mitigation: the
`FilesystemStore` refactor lands first and alone, with a byte-for-byte
comparison test against a fixture store.

---

## M2 — Observability

**Goal:** make the engine operable.

**Plan:**
1. Replace the three bare `print(..., file=sys.stderr)` calls
   (`memory.py:1643`, `:1690`, `:1698`) with a `logging` logger under
   `mem20.memory_engine`, structured (JSON formatter opt-in via
   `MEM20_LOG_FORMAT=json`).
2. Counters: `remember_total{status}`, `recall_total{surface}`,
   `index_drift_total{index}`, `write_refused_total{reason}`.
3. `MemoryEngine.health()` already returns a `HealthReport` — expose it as
   `GET /healthz` (liveness) and `GET /readyz` (index consistency) in the
   gateway increment.
4. Optional OpenTelemetry span around `remember` / `recall_hybrid`.

**Acceptance:** no `print()` remains in the write path; a log line is emitted
per write with `topic`, `id`, `epistemic_status`, and duration; metrics are
exportable without a hard dependency (no-op if the client is absent).

---

## M3 — Python SDK

**Goal:** a `mem20-memory` package that depends only on the declared surface.

**Plan:**
1. `sdk/python/` with `Mem20MemoryClient` — thin wrapper over `MemoryEngine`
   plus an HTTP transport for the REST surface (M4).
2. Generated from `memory_engine.__all__` so the SDK cannot drift from the
   contract.
3. Publish `py.typed`.

**Acceptance:** SDK imports nothing from `memory_engine.memory` directly; a
contract test asserts every `__all__` name has an SDK counterpart.

---

## M4 — REST v1

**Goal:** `POST /v1/facts`, `GET /v1/facts`, `GET /v1/facts/{id}`,
`POST /v1/recall`, `GET /v1/health`.

**Plan:**
1. FastAPI app in `gateway/` (already the designated home).
2. Every error maps to a status via `MemoryEngineError.to_dict()` — the typed
   error model from M0 is what makes this a table lookup instead of string
   matching.
3. `Idempotency-Key` header honoured via `idempotency_key()`.
4. Version prefix `/v1`; breaking changes go to `/v2`, never in place.

**Acceptance:** OpenAPI schema generated; contract tests run against the live
app; a duplicate `Idempotency-Key` returns the original record, not a new one.

**Gate:** requires M0 + M1 + M2.

---

## M5 — CLI hardening

**Goal:** make the existing CLI scriptable.

**Plan:**
1. `--json` on every subcommand (machine-readable output).
2. Exit codes: `0` ok, `2` validation, `3` not found, `4` store unavailable.
3. `--version` from `memory_engine.__version__`.
4. Console entry point `mem20-memory` in `pyproject.toml`.

**Acceptance:** `mem20-memory remember --json` emits one JSON object; exit codes
asserted in tests.

---

## M6 — Test hardening

**Goal:** close the test gaps recorded in `GAP-INVENTORY.md`.

**Plan:**
1. Fix D3: add `_detect_only` to the root `memory.py` shim re-exports.
2. Fix D4: mark dependency-requiring tests `@pytest.mark.integration`.
3. Fuzz `detect_secrets` / `redact_secrets` with Hypothesis text strategies —
   the property is "redaction never raises and never leaves a detected secret".
4. Benchmarks: `remember` p50/p99, `recall_hybrid` p50/p99, with a budget file.

**Acceptance:** `pytest memory_engine/tests` is green with and without optional
deps; fuzz runs 1,000 examples clean; benchmark budget committed.

---

## M7 — Documentation

**Plan:** API reference generated from `__all__` docstrings; ADRs for the
grounded/simulated firewall, the bi-temporal model, and the facade-delegates
decision; migration note for consumers moving off `memory_engine.memory`.

---

## M8 — Packaging / release

**Plan:**
1. Fix D1: single-source the version from `VERSION` into `pyproject.toml`
   (setuptools `dynamic = ["version"]`).
2. Fix D2: remove `memory.py.broken` (needs owner sign-off — tracked file).
3. Container image, CI matrix (3.11/3.12), release checklist.

**Gate:** requires M0–M2.

---

## Ordering rationale

M0 first because every other surface needs a contract to build against — an SDK
or a REST layer over an undeclared 4,800-line module just moves the coupling.
M1 second because persistence is the highest-risk refactor and benefits from
landing while the test suite is still small. M2 before M4 because a REST service
you cannot observe is not operable. M4 and M8 are gated on M0–M2 as the
orchestrator specified.
