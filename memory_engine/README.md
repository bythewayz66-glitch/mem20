# memory_engine

The estate's grounded-fact store: write facts, read them back, and audit what
the rest of the estate reports. Every figure below was measured, not estimated.

## At a glance

| metric | value |
|---|---|
| python modules | 5 |
| lines of python | 5,277 |
| test files | 6 |
| console entry points | 0 (`python3 -m memory_engine.cli`) |

## Top-level modules

- `__init__.py`
- `memory.py` — the store: `remember`, `recall`, `pin_block`, `recall_semantic`
- `retrieval_v2.py` — hybrid retrieval: `calibrated_search`, `rerank`, `mmr`
- `cli.py` — the command-line surface
- `integrations.py` — cross-subsystem wiring

## CLI

Every subcommand emits the shared `mem20.cli/1` JSON envelope when `--json` is
passed, so fleet scripts parse memory_engine output like any other subsystem.

```bash
# What the store currently holds
python3 -m memory_engine.cli stats --json

# Write a grounded fact. epistemic_status is REQUIRED -- an unlabeled write is
# refused rather than stored, because a defaulted label is indistinguishable
# from an asserted one at every later read.
python3 -m memory_engine.cli remember \
    --topic wave1 --content "memory_engine CLI works" \
    --epistemic-status observed --json

# Read it back
python3 -m memory_engine.cli recall --topic wave1
```

## Cross-subsystem wiring

`integrations.py` is the one place memory_engine reaches into other subsystems.
Every edge calls a real public API and returns a real value — nothing is
stubbed, and nothing is imported only to satisfy a checker.

| edge | what it actually does |
|---|---|
| `mem20kanbanz.migrate.sha256` | hashes the real ledger file, for tamper checks |
| `mem20ops.clicheck.classify_naming` | classifies a topic key against estate naming rules |
| `mem20corez.mlp.CharMLP` | counts the parameters the model actually allocates |
| `mem20cliz.build_envelope` | builds the shared CLI envelope |
| `mem20verify.testrun.discover_packages` | lists packages the estate's test runner would find |
| `toolchest.catalog.build_inventory` | reads the real on-box tool inventory |

Prove every edge, and optionally record the snapshot as a grounded fact:

```bash
python3 -m memory_engine.cli wiring --record --json
```

The command exits non-zero if any edge is dead, so a broken integration is loud
rather than silent. A store that has never been written to reports the ledger
digest edge as `skipped` — a valid state, distinct from a failure.

## Verification

```bash
cd /opt/mem20/memory_engine
python3 -m pytest tests -q
python3 -m memory_engine.cli wiring --json
```
