# core.py duplication (issue #17)

## Status
~100 `mem20*z/*/core.py` files are byte-identical (template scaffolding).

## Completion plan (do not delete packages)
1. Extract shared body into `mem20corez` (or `corez`).
2. Each identical `core.py` becomes:
   ```python
   from mem20corez import *  # noqa: F401,F403
   ```
3. Keep divergent copies (`mem20wasmz`, `mem20webgpuz`) as-is.
4. Add CI: fail if a new byte-identical copy appears without the re-export.

This is a coordinated multi-PR change; document here until landed.
