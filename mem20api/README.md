# mem20api

A stable Python API over the mem20 memory engine.

## Why this exists

The engine (`memory_engine/memory.py`) resolves every store path at import time:

```python
STORE_DIR = os.environ.get("MEM20_STORE_PATH") or os.path.expanduser("~/.mem20/store")
LEDGER = os.path.join(STORE_DIR, "ledger.jsonl")
```

Callers therefore had to reassign a dozen module globals before every operation, and the MCP handlers were running `sys.path.insert(...)` plus a fresh `from memory import ...` inside each query. That is a lot of machinery to answer "what is in my memory".

This package is the supported way in.

## Install

```bash
pip install -e /path/to/mem20/mem20api
# optional retrieval extras:
pip install -e '/path/to/mem20/mem20api[retrieval]'
```

## Use

```python
from mem20api import open_store

with open_store() as store:
    store.remember("deploys", "Prod runs build 4127", tags=["prod"])

    r = store.semantic("what build is prod on", k=5)
    r["hits"]
    r["healthy"]        # must be True in healthy production
    r["diagnostic"]

    store.graph("prod", hops=2)
    store.health()
    store.contamination()  # guaranteed 0.0 on a clean engine
```

## Guarantees

**Contamination rate is `0.0`.** Simulated content never reaches grounded indexes. This is structural, not aspirational.

**Index drift is a defect.** Diagnostics exist so you can detect disagreement between FAISS/BM25 and the ledger and **rebuild**. Healthy state is `healthy == True` and zero stale pointers — not “we admit drift forever.”

**Reads never write** the ledger. **Promotion requires evidence.**

## API

| Method | Kind | Notes |
|---|---|---|
| `health()` | read | Index/ledger agreement |
| `contamination()` | read | Must be `0.0` when clean |
| `recall` / `semantic` / `hybrid` / `graph` | read | Retrieval |
| `remember` / `remember_simulated` / `promote` / `supersede` | write | Partition-safe |
| `rebuild(which)` | derived | Reindex from ledger |

## Multi-language clients

MCP clients for Ruby, Perl, TypeScript, Godot, and C++ are documented in [SDKS.md](../SDKS.md).

## License

MIT.
