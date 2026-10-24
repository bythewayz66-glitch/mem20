---
applyTo: "**/*.py"
---

# Python rules for mem20

Target **Python >= 3.10**; CI runs **3.11**. Match the surrounding style; this
codebase favours explicit, defensive code over clever one-liners.

## Imports and package shadowing

The repo root on `sys.path` lets nested project directories win as **namespace
packages**. Consequences to respect:

- `mcp/` collides with the `mcp` SDK. Inside `mcp/`, import the SDK as
  `from mcp.server import Server` **only** after the real SDK is bound
  (as `conftest.py` does). Never add a module-scope `import mcp` in a file that
  pytest may import during collection.
- If you add a new `mem20*z` project directory, keep the real package at
  `<project>/<name>/__init__.py` or `<project>/src/<name>/__init__.py` so
  `conftest.py`'s `_importable()` can find it.
- Do not add `__init__.py` to an outer project directory to fix an ImportError.

## Memory engine invariants

When touching `memory_engine/`, `memory.py`, or `mcp/memory_tools.py`:

- Every write path must assert grounded before touching a vector or BM25 index.
- `_allow_simulated` stays rejected. Do not add a keyword that bypasses it.
- Promotion requires evidence (resolved prediction or registered verifier).
- Retrieval results keep `healthy` and `diagnostic` keys. Removing them is a
  regression even if every test still passes.

## Errors and exit codes

- Do not call `sys.exit()` from library code. `mcp/memory_tools.py` does so on
  ImportError, which kills the pytest session; treat that as a known wart, not a
  pattern to copy.
- Prefer raising a typed exception with a clear message over returning `None`.
- Never widen an `except` to `except Exception:` to make a test pass.

## Tests

- Place tests in `<project>/tests/` or the root `tests/`.
- Mark fast tests `@pytest.mark.unit` and anything needing torch, blender, a live
  network, or a running server `@pytest.mark.integration`.
- Run narrowly: `python3 -m pytest <package> -q`. A bare `pytest` walks the estate.
- Do not use `tmp_path` for anything the store persists — the store has its own
  paths and a per-test venv/timeout story via `mem20verify`.

## Hygiene

- No new generated files in git. `*.faiss`, `ledger.jsonl`, `entries/*.json`,
  `memory.db*` and `__pycache__` are gitignored for a reason.
- Keep `pyproject.toml` `py-modules` accurate if you add a root-level module.
