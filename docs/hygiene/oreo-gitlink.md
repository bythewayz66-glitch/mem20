# mem20oreo / OREO wiring (issues #30 / #31)

## Status
`mem20oreo` used to be a dangling gitlink (404) and was removed in 71939ee so
the Pages checkout works. The OREO engine lives in its own public repo:
<https://github.com/JaysonAIOnline/oreo> (the `mem20oreo` package at the repo root).

## How it is wired
- `mem20agentz` declares it as the `oreo` extra, pinned to a commit:
  `mem20oreo @ git+https://github.com/JaysonAIOnline/oreo.git@51876da...`
- Install: `pip install "./mem20agentz[dev,oreo]"` (or `mem20agentz[oreo]`).
- No submodule / gitlink is used, so the gitlink guard and Pages stay clean.
- `test_oreo.py`, `test_oreditor.py`, `test_graphstore.py` import `mem20oreo`
  directly - no `importorskip`. A missing OREO install is a real failure.
- `test_react_editor_build_served` needs the React bundle:
  `cd mem20agentz/web && npm ci && npm run build` (output is gitignored).
- CI: a `mem20agentz` job (clean install with `[dev,oreo]`, React build, pytest) is proposed in PR for #30.

## Bumping OREO
Update the commit SHA in `mem20agentz/pyproject.toml` (`oreo` extra) and rerun
`pytest mem20agentz/tests`.

See `docs/audit/2026-10-gitlink-audit.md` for the history.
