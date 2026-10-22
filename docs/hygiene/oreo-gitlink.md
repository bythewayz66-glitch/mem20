# mem20oreo / OREO wiring (issues #30 / #31)

## Status
`mem20oreo` was a dangling gitlink (404). Content is not in this monorepo as a
normal package. Imports in `mem20agentz` expect `mem20oreo`.

## Policy
- **Do not invent** a stub package that pretends to be the real OREO engine.
- Soft-fail: tests use `pytest.importorskip("mem20oreo")`.
- Runtime: clear `ImportError` pointing at this doc and the gitlink audit.
- When a real remote exists: `git submodule add <url> mem20oreo` (or vendor).

See `docs/audit/2026-10-gitlink-audit.md`.
