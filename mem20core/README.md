# `mem20core` — standalone core package — `mem20core/`

A self-contained, dependency-light slice of the memory core, packaged for
installation on its own (`pyproject.toml`).

**4 tracked file(s).**

## Contents

- `mem20core/core.py` — schema version, validation, safety and cancellation errors, store and HTTP surface
- `mem20core/fixes.py` — compatibility fixes applied on top of the core
- `pyproject.toml` — package metadata

## Usage

```bash
pip install -e mem20core
```

## Notes

This is a packaged subset. The full engine lives in `memory_engine/`; changes to
shared behaviour must land in both or be explicitly reconciled.

---

Part of the [mem20 monorepo](../README.md). See [`docs/INDEX.md`](../docs/INDEX.md) for the full documentation map.
